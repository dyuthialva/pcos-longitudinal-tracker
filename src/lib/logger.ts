/** Production builds must not print clinical payloads. */
export function debugLog(..._args: unknown[]): void {
  if (import.meta.env.DEV) {
    // Intentionally unused in production; keep signature for call sites.
  }
}
