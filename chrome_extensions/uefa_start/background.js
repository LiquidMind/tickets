// Set up a persistent message port
const port = chrome.runtime.connect({ name: "test" });
//// Check if Tampermonkey is running
//chrome.runtime.getBackgroundPage().then((backgroundPage) => {
//  const tampermonkeyRunning = !!backgroundPage.TM || false;
//  console.log("Tampermonkey running:", tampermonkeyRunning);
//});
chrome.runtime.onMessageExternal.addListener(
  function(request, sender, sendResponse) {
    chrome.runtime.sendMessage('ijgahfpilangnbelgacoegbofdlcdpce', {type: "test_answ"}, (response) => {
        // Send the response back through the message port
        port.postMessage({ type: "test", response });
      });
  });

// Listen for messages from the content script
port.onMessage.addListener((message, sender) => {

  if (message.type === "checkScript") {
    // Check if the script is installed
    chrome.runtime.sendMessage(
      "dhdgffkkebhmkfjojejmpbldmpobfkfo",
      {
        type: "getScript",
        script: {
          id: message.script.id
        }
      },
      (response) => {
        // Send the response back through the message port
        port.postMessage({ type: "checkScriptResult", result: !!response });
      }
    );
  } else if (message.type == "test"){
//    chrome.runtime.sendMessage("dhdgffkkebhmkfjojejmpbldmpobfkfo", {getTargetData: true},
//      function(response) {
//        if (targetInRange(response.targetData))
//           port.postMessage({ type: "test_answ", result: response.targetData });
//      });
        port.postMessage({ type: "test_answ", result: 'response.targetData '});
  } else {
    // Forward the message to Tampermonkey
    chrome.runtime.sendMessage(
      "dhdgffkkebhmkfjojejmpbldmpobfkfo",
      message,
      (response) => {
        // Send the response back through the message port
        port.postMessage({ type: "tampermonkeyResponse", response });
      }
    );
  }
});
