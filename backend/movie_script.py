"""4-stage Movie Script Generation workflow."""

import re
from typing import List, Dict, Any, Tuple, AsyncGenerator
from .openrouter import query_models_parallel, query_model
from .config import COUNCIL_MODELS, MOVIE_SCRIPT_DEFAULT_TURNS


async def stage1_generate_scripts(user_prompt: str) -> List[Dict[str, Any]]:
    """
    Stage 1: Each model creates their own script (outline + key scenes).

    Args:
        user_prompt: The user's movie idea/description

    Returns:
        List of dicts with 'model' and 'response' keys
    """
    script_prompt = f"""You are a professional screenwriter. Create a movie script based on the following idea:

{user_prompt}

Provide your script in the following format:

**TITLE:** A compelling movie title

**LOGLINE:** One-sentence summary (25 words max)

**GENRE:** Primary genre and any secondary genres

**OUTLINE:**
- ACT 1 (Setup): Key plot points
- ACT 2 (Confrontation): Key plot points
- ACT 3 (Resolution): Key plot points

**KEY SCENES:** Write 3-5 of the most important scenes with:
- Scene heading (INT/EXT, LOCATION - TIME)
- Action lines describing what happens
- Character dialogue

Format your response as a professional screenplay excerpt. Be creative and specific with your choices."""

    messages = [{"role": "user", "content": script_prompt}]

    # Query all models in parallel
    responses = await query_models_parallel(COUNCIL_MODELS, messages)

    # Format results
    stage1_results = []
    for model, response in responses.items():
        if response is not None:
            stage1_results.append({
                "model": model,
                "response": response.get('content', '')
            })

    return stage1_results


async def stage2_peer_review(
    user_prompt: str,
    stage1_results: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model reviews and ranks the anonymized scripts.

    Args:
        user_prompt: The original user prompt
        stage1_results: Results from Stage 1

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    # Create anonymized labels for scripts (Script A, Script B, etc.)
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to model name
    label_to_model = {
        f"Script {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    # Build the ranking prompt
    scripts_text = "\n\n" + "="*60 + "\n\n".join([
        f"\n\nScript {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are evaluating different MOVIE SCRIPTS for the following prompt:

Original Request: {user_prompt}

Here are the scripts from different writers (anonymized):
{scripts_text}

Your task:
1. First, evaluate each script individually. Consider:
   - Story structure and pacing
   - Character development and dialogue quality
   - Visual storytelling and cinematic potential
   - Originality and creative choices
   - How well it captures the original request

2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the scripts from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the script label (e.g., "1. Script A")
- Do not add any other text or explanations in the ranking section

Example format:
Script A has strong dialogue but weak pacing...
Script B shows excellent character development...

FINAL RANKING:
1. Script B
2. Script A
3. Script C

Now provide your evaluation and ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    # Get rankings from all council models in parallel
    responses = await query_models_parallel(COUNCIL_MODELS, messages)

    # Format results
    stage2_results = []
    for model, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            parsed = parse_script_ranking(full_text)
            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed
            })

    return stage2_results, label_to_model


def parse_script_ranking(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of script labels in ranked order
    """
    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Script A")
            numbered_matches = re.findall(r'\d+\.\s*Script [A-Z]', ranking_section)
            if numbered_matches:
                return [re.search(r'Script [A-Z]', m).group() for m in numbered_matches]

            # Fallback: Extract all "Script X" patterns in order
            matches = re.findall(r'Script [A-Z]', ranking_section)
            return matches

    # Fallback: try to find any "Script X" patterns in order
    matches = re.findall(r'Script [A-Z]', ranking_text)
    return matches


def calculate_script_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models for scripts.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking['ranking']
        parsed_ranking = parse_script_ranking(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


async def stage3_select_best_script(
    user_prompt: str,
    stage1_results: List[Dict[str, Any]],
    aggregate_rankings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Stage 3: Select the best script direction (not synthesis).

    Args:
        user_prompt: The original user prompt
        stage1_results: Individual scripts from Stage 1
        aggregate_rankings: Calculated rankings from Stage 2

    Returns:
        Dict with winning script info and collaborators for Stage 4
    """
    if not aggregate_rankings:
        return {
            "winning_model": "error",
            "winning_script": "No scripts were ranked.",
            "collaborators": [],
            "selection_rationale": "Unable to determine winner - no rankings available."
        }

    # Get top 2 models from aggregate rankings
    top2_models = [r['model'] for r in aggregate_rankings[:2]]

    # Find winning model and script
    winning_model = aggregate_rankings[0]['model']
    winning_script = next(
        (r['response'] for r in stage1_results if r['model'] == winning_model),
        "Script not found"
    )

    # Build selection rationale
    rationale = f"Selected **{winning_model.split('/')[-1]}**'s script based on peer review rankings.\n\n"
    rationale += "**Ranking Results:**\n"
    for i, r in enumerate(aggregate_rankings[:3], 1):
        model_short = r['model'].split('/')[-1]
        rationale += f"{i}. {model_short} - Average rank: {r['average_rank']:.2f} ({r['rankings_count']} votes)\n"

    if len(top2_models) >= 2:
        collaborators_short = [m.split('/')[-1] for m in top2_models]
        rationale += f"\n**Stage 4 Collaborators:** {collaborators_short[0]} and {collaborators_short[1]} will refine the winning script together."

    return {
        "winning_model": winning_model,
        "winning_script": winning_script,
        "collaborators": top2_models,
        "selection_rationale": rationale
    }


class CollaborativeDialogue:
    """
    Manages multi-turn dialogue between top 2 models to refine a script.
    """

    def __init__(
        self,
        model_a: str,
        model_b: str,
        winning_script: str,
        user_prompt: str,
        num_turns: int = MOVIE_SCRIPT_DEFAULT_TURNS
    ):
        self.model_a = model_a  # Winner (primary author)
        self.model_b = model_b  # Runner-up (collaborator)
        self.winning_script = winning_script
        self.user_prompt = user_prompt
        self.num_turns = num_turns
        self.dialogue_history: List[Dict[str, Any]] = []
        self.conversation_context_a: List[Dict[str, str]] = []
        self.conversation_context_b: List[Dict[str, str]] = []

    def _initialize_context(self):
        """Initialize conversation context for both models."""
        base_context = f"""You are collaborating on refining a movie script.

Original Request: {self.user_prompt}

The Winning Script:
{self.winning_script}

Your goal is to work together to improve this script through constructive dialogue. Focus on:
- Strengthening weak scenes
- Improving dialogue
- Enhancing character development
- Tightening the narrative structure
- Adding cinematic moments

Be specific with your suggestions - reference exact scenes, characters, and dialogue."""

        self.conversation_context_a = [{"role": "system", "content": base_context}]
        self.conversation_context_b = [{"role": "system", "content": base_context}]

    async def run_dialogue(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute the collaborative dialogue, yielding each turn for streaming.

        Yields:
            Dict with turn info: {turn, model, role, message}
        """
        self._initialize_context()

        for turn in range(1, self.num_turns + 1):
            # Model A (winner/author) speaks
            turn_a = await self._execute_turn_a(turn)
            self.dialogue_history.append(turn_a)
            yield turn_a

            # Model B (collaborator) responds
            turn_b = await self._execute_turn_b(turn)
            self.dialogue_history.append(turn_b)
            yield turn_b

    async def _execute_turn_a(self, turn: int) -> Dict[str, Any]:
        """Execute Model A's turn (the author)."""
        if turn == 1:
            prompt = """As the author of this script, review your work and identify 2-3 specific areas you'd like to improve or expand. What aspects could be stronger? Where would you like fresh perspective?"""
        else:
            prompt = """Consider the collaborator's suggestions. Which ideas resonate with you? How would you incorporate them? Are there any suggestions you'd modify or push back on? Share your thoughts and any new ideas that emerged."""

        self.conversation_context_a.append({"role": "user", "content": prompt})

        response = await query_model(self.model_a, self.conversation_context_a)
        content = response.get('content', '') if response else "Unable to generate response."

        self.conversation_context_a.append({"role": "assistant", "content": content})
        # Share with Model B
        self.conversation_context_b.append({"role": "user", "content": f"The author says:\n\n{content}"})

        return {
            "turn": turn,
            "model": self.model_a,
            "role": "author",
            "message": content
        }

    async def _execute_turn_b(self, turn: int) -> Dict[str, Any]:
        """Execute Model B's turn (the collaborator)."""
        if turn == 1:
            prompt = """Review the script and the author's thoughts. Offer specific, constructive suggestions for improvement. Focus on areas the author mentioned, but also share any other ideas you have to make this script stronger."""
        else:
            prompt = """Building on the ongoing discussion, offer your perspective. Do you agree with the author's direction? What additional refinements would you suggest? Be specific about scenes, dialogue, or structural changes."""

        self.conversation_context_b.append({"role": "user", "content": prompt})

        response = await query_model(self.model_b, self.conversation_context_b)
        content = response.get('content', '') if response else "Unable to generate response."

        self.conversation_context_b.append({"role": "assistant", "content": content})
        # Share with Model A
        self.conversation_context_a.append({"role": "user", "content": f"The collaborator suggests:\n\n{content}"})

        return {
            "turn": turn,
            "model": self.model_b,
            "role": "collaborator",
            "message": content
        }

    async def generate_final_script(self) -> str:
        """
        Generate the final refined script after dialogue completes.
        Model A (the author) produces the final version.
        """
        final_prompt = """Based on our collaborative discussion, produce the FINAL REFINED SCRIPT.

Incorporate the best ideas from our dialogue. Present the complete refined script in proper screenplay format:

**TITLE:**
**LOGLINE:**
**GENRE:**

**REFINED OUTLINE:**
- ACT 1:
- ACT 2:
- ACT 3:

**KEY SCENES:** (Write out the improved/refined key scenes with proper formatting)

Make this the best version of the script, synthesizing our collaborative improvements."""

        self.conversation_context_a.append({"role": "user", "content": final_prompt})

        response = await query_model(self.model_a, self.conversation_context_a, timeout=180.0)

        if response:
            return response.get('content', 'Unable to generate final script.')
        return "Unable to generate final script."

    def get_results(self) -> Dict[str, Any]:
        """Get the complete dialogue results."""
        return {
            "dialogue_history": self.dialogue_history,
            "collaborators": [self.model_a, self.model_b],
            "num_turns": self.num_turns
        }


async def run_movie_script_workflow(
    user_prompt: str,
    num_turns: int = MOVIE_SCRIPT_DEFAULT_TURNS
) -> Dict[str, Any]:
    """
    Run the complete 4-stage movie script workflow.

    Args:
        user_prompt: The user's movie idea
        num_turns: Number of dialogue turns for Stage 4

    Returns:
        Dict with all stage results and metadata
    """
    # Stage 1: Generate scripts
    stage1_results = await stage1_generate_scripts(user_prompt)

    if not stage1_results:
        return {
            "stage1": [],
            "stage2": [],
            "stage3": {"winning_model": "error", "winning_script": "All models failed.", "collaborators": [], "selection_rationale": "Error"},
            "stage4": {"dialogue_history": [], "refined_script": "", "num_turns": 0},
            "metadata": {}
        }

    # Stage 2: Peer review
    stage2_results, label_to_model = await stage2_peer_review(user_prompt, stage1_results)
    aggregate_rankings = calculate_script_rankings(stage2_results, label_to_model)

    # Stage 3: Select best script
    stage3_result = await stage3_select_best_script(user_prompt, stage1_results, aggregate_rankings)

    # Stage 4: Collaborative dialogue
    if len(stage3_result['collaborators']) >= 2:
        dialogue = CollaborativeDialogue(
            model_a=stage3_result['collaborators'][0],
            model_b=stage3_result['collaborators'][1],
            winning_script=stage3_result['winning_script'],
            user_prompt=user_prompt,
            num_turns=num_turns
        )

        # Run dialogue
        async for _ in dialogue.run_dialogue():
            pass  # In non-streaming mode, just run through

        # Generate final script
        refined_script = await dialogue.generate_final_script()

        stage4_result = {
            "dialogue_history": dialogue.dialogue_history,
            "refined_script": refined_script,
            "collaborators": stage3_result['collaborators'],
            "num_turns": num_turns
        }
    else:
        stage4_result = {
            "dialogue_history": [],
            "refined_script": stage3_result['winning_script'],
            "collaborators": stage3_result['collaborators'],
            "num_turns": 0
        }

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings
    }

    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "stage4": stage4_result,
        "metadata": metadata
    }
