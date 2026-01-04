#!/bin/bash
# Helper script to run LLM Council tests

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")"

echo -e "${YELLOW}LLM Council Test Runner${NC}"
echo "========================================"

# Check if backend is running
echo -e "\n${YELLOW}Checking if backend server is running...${NC}"
if curl -s http://localhost:8004/api/conversations > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server is running${NC}"
else
    echo -e "${RED}✗ Backend server is not running${NC}"
    echo -e "  Please start the backend first:"
    echo -e "  ${YELLOW}python -m backend.main${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "  Please create a .env file with OPENROUTER_API_KEY"
    exit 1
fi

# Check if OPENROUTER_API_KEY is set
if ! grep -q "OPENROUTER_API_KEY" .env; then
    echo -e "${YELLOW}⚠ Warning: OPENROUTER_API_KEY not found in .env${NC}"
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    quick)
        echo -e "\n${YELLOW}Running quick server check...${NC}"
        pytest backend/tests/test_movie_script_integration.py::test_server_is_running -v
        ;;
    integration)
        echo -e "\n${YELLOW}Running integration tests...${NC}"
        echo -e "${YELLOW}⚠ This will take 10-15 minutes and make real API calls${NC}"
        pytest backend/tests/ -m integration -v
        ;;
    slow)
        echo -e "\n${YELLOW}Running slow tests...${NC}"
        echo -e "${YELLOW}⚠ This will take 10-15 minutes and make real API calls${NC}"
        pytest backend/tests/ -m slow -v
        ;;
    full)
        echo -e "\n${YELLOW}Running full integration test...${NC}"
        echo -e "${YELLOW}⚠ This will take 10-15 minutes and make real API calls${NC}"
        pytest backend/tests/test_movie_script_integration.py::test_movie_script_workflow_end_to_end -v
        ;;
    all)
        echo -e "\n${YELLOW}Running all tests...${NC}"
        pytest backend/tests/ -v
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: ./run_tests.sh [TEST_TYPE]"
        echo ""
        echo "TEST_TYPE options:"
        echo "  quick       - Quick server connectivity check (< 1 min)"
        echo "  integration - All integration tests (10-15 min)"
        echo "  slow        - All slow tests (10-15 min)"
        echo "  full        - Full end-to-end movie script test (10-15 min)"
        echo "  all         - All tests (default)"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Test run complete!${NC}"
