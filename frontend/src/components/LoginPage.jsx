import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../contexts/AuthContext';
import './LoginPage.css';

/**
 * Login page with Google Sign-In button.
 */
function LoginPage() {
  const { login } = useAuth();

  const handleSuccess = (credentialResponse) => {
    login(credentialResponse);
  };

  const handleError = () => {
    console.error('Google Login Failed');
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <h1 className="login-title">LLM Council</h1>
        <p className="login-subtitle">
          Collaborative AI deliberation with multiple LLMs
        </p>
        <div className="login-button-container">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={handleError}
            useOneTap
            theme="outline"
            size="large"
            text="signin_with"
            shape="rectangular"
          />
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
