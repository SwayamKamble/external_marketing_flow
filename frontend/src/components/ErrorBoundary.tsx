import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertCircle, RefreshCw, Copy, Check } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  copied: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
    copied: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null, copied: false };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  private handleCopy = async () => {
    if (!this.state.error) return;
    const errorDetails = `Error: ${this.state.error.message}\n\nStack Trace:\n${this.state.error.stack || "N/A"}\n\nComponent Stack:\n${this.state.errorInfo?.componentStack || "N/A"}`;
    try {
      await navigator.clipboard.writeText(errorDetails);
      this.setState({ copied: true });
      setTimeout(() => this.setState({ copied: false }), 2000);
    } catch (e) {
      console.error("Failed to copy error logs", e);
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-3xl mx-auto my-12 bg-white rounded-2xl border border-red-100 shadow-xl overflow-hidden">
          <div className="bg-red-50 border-b border-red-100 p-6 flex items-center gap-4">
            <div className="p-3 bg-red-100 rounded-full text-red-600">
              <AlertCircle size={28} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-red-900">Something went wrong</h2>
              <p className="text-sm text-red-600 mt-0.5">The Content Review page encountered a rendering error.</p>
            </div>
          </div>

          <div className="p-6 flex flex-col gap-6">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">Error Message</span>
              <p className="text-slate-800 font-mono text-sm break-all font-semibold">
                {this.state.error?.message || "Unknown rendering exception"}
              </p>
            </div>

            {this.state.errorInfo && (
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Error Details</span>
                  <button
                    onClick={this.handleCopy}
                    className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 font-medium transition"
                  >
                    {this.state.copied ? (
                      <>
                        <Check size={13} className="text-emerald-600" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy size={13} />
                        Copy Error Logs
                      </>
                    )}
                  </button>
                </div>
                <div className="bg-slate-950 text-slate-300 p-4 rounded-lg text-xs font-mono whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed border border-slate-900">
                  {this.state.error?.stack || "No trace available"}
                  {this.state.errorInfo.componentStack}
                </div>
              </div>
            )}

            <div className="flex gap-3 justify-end border-t border-slate-100 pt-6">
              <button
                onClick={() => window.location.reload()}
                className="flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-bold py-2.5 px-6 rounded-lg transition text-sm"
              >
                <RefreshCw size={15} />
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
