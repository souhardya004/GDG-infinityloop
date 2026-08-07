import { useEffect, useState, useRef } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { AlertCircle, ArrowLeft, Hexagon, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function OAuthCallbackPage() {
  const { provider } = useParams<{ provider: string }>();
  const [searchParams] = useSearchParams();
  const code = searchParams.get("code");
  const errorParam = searchParams.get("error");
  const errorDesc = searchParams.get("error_description");

  const { oauthLogin } = useAuth();
  const navigate = useNavigate();

  const [errorMessage, setErrorMessage] = useState<string | null>(
    errorParam ? errorDesc || errorParam : null,
  );
  const [processing, setProcessing] = useState(true);
  const attemptedRef = useRef(false);

  useEffect(() => {
    if (attemptedRef.current) return;
    if (errorParam) {
      setProcessing(false);
      return;
    }

    if (!code || (provider !== "github" && provider !== "google")) {
      setErrorMessage("Invalid authentication callback parameters.");
      setProcessing(false);
      return;
    }

    attemptedRef.current = true;
    const redirectUri = `${window.location.origin}/auth/callback/${provider}`;

    oauthLogin(provider, { code, redirect_uri: redirectUri })
      .then(() => {
        navigate("/projects", { replace: true });
      })
      .catch((err: any) => {
        setErrorMessage(
          err?.message || `Failed to authenticate with ${provider}. Please try signing in again.`,
        );
        setProcessing(false);
      });
  }, [code, provider, errorParam, errorDesc, oauthLogin, navigate]);

  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/20 text-accent-soft ring-1 ring-accent/30 shadow-lg shadow-accent/10 mb-6">
          <Hexagon className="h-6 w-6" />
        </div>

        {processing && !errorMessage ? (
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-accent mb-4" />
            <h2 className="text-lg font-semibold text-white">Completing sign in...</h2>
            <p className="mt-2 text-xs text-white/60">
              Verifying your credentials with {provider === "github" ? "GitHub" : "Google"}...
            </p>
          </div>
        ) : (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 backdrop-blur-xl">
            <AlertCircle className="mx-auto h-8 w-8 text-red-400 mb-4" />
            <h2 className="text-lg font-semibold text-white">Authentication Failed</h2>
            <p className="mt-2 text-xs text-red-200/80 mb-6 leading-relaxed">
              {errorMessage || "An unexpected error occurred during login."}
            </p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-white/20"
            >
              <ArrowLeft className="h-4 w-4" />
              Return to Sign In
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
