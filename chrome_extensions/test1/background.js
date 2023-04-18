//const port = chrome.runtime.connect({ name: "testport" });
const port = chrome.runtime.connect('nppmangmiihgijobebplbjcapcbnnidg');
chrome.runtime.onConnect.addListener(function(port) {
    console.log(port.name);
    port.onMessage.addListener((message, sender) => {
      if (message.type === "testScript") {
        // Send the response back through the message port
        port.postMessage({ type: "testScriptResponse", result: 'testScriptResponse' });

      } else {
        // Forward the message to Tampermonkey
        port.postMessage({ type: "unknown", result: "unknown script" });
      }
    });
});