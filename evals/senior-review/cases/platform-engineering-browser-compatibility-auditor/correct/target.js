// Supported host contract: WebView has no showOpenFilePicker; nativeOpenDocument exists and returns a document. Requirement: Open works on it.
export async function chooseFile(host) {
  return typeof host.showOpenFilePicker === "function" ? host.showOpenFilePicker() : host.nativeOpenDocument();
}
