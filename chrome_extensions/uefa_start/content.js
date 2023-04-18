// Define the user script code
const scriptCode = `
// ==UserScript==
// @name My User Script
// @namespace my-userscript
// @version 1
// @grant none
// ==/UserScript==

console.log("Hello, Tampermonkey!");
`;

// Set up a message port to communicate with the background script
//const port = chrome.runtime.connect({ name: "tampermonkey" });
const port = chrome.runtime.connect({ name: "test" });

// Send a message to check if the script is already installed
//port.postMessage({ type: "checkScript", script: { id: "my-userscript" } });
port.postMessage({ type: "test" });

// Listen for the response from the background script
port.onMessage.addListener((message, sender) => {
  if (message.type === "checkScriptResult") {
    if (message.result) {
      console.log("Script already installed!");
    } else {
      // Send a message to add the script if it's not already installed
      port.postMessage({ type: "addScript", script: { code: scriptCode } });
    }
  } else if (message.type === "tampermonkeyResponse") {
    console.log("Response from Tampermonkey:", message.response);
  } else if (message.type === "test_answ") {
    console.log("Response from test:", message.response);
  }
});
