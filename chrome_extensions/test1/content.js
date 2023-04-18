//const port = chrome.runtime.connect({ name: "testport" });
const port = chrome.runtime.connect('nppmangmiihgijobebplbjcapcbnnidg');

port.postMessage({ type: "testScript", data: { id: "test ID" } });

port.onMessage.addListener((message, sender) => {
  if (message.type === "testScriptResponse") {
    if (message.result) {
      console.log("Result from background", message);
    } else {
      // Send a message to add the script if it's not already installed
      console.log("No result from background", message);
    }
  }
});