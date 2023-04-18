function displayExtensions(extensions) {

  const container = document.getElementById('extensions');
  extensions.forEach((extension) => {

    console.log(extension);
    const item = document.createElement('div');
    const title = document.createElement('h3');
    title.textContent = extension.name;
    if(extension.name == 'Tampermonkey'){
        for(key in extension){
            console.log(extension[key]);
            title.textContent += extension[key];
        }
    }
    item.appendChild(title);

    const enableButton = document.createElement('button');
    enableButton.textContent = extension.enabled ? 'Disable' : 'Enable';
    enableButton.onclick = () => {
      chrome.management.setEnabled(extension.id, !extension.enabled, () => {
        location.reload();
      });
    };
    item.appendChild(enableButton);

    const uninstallButton = document.createElement('button');
    uninstallButton.textContent = 'Uninstall';
    uninstallButton.onclick = () => {
      chrome.management.uninstall(extension.id, { showConfirmDialog: true }, () => {
        location.reload();
      });
    };
    item.appendChild(uninstallButton);

    container.appendChild(item);
  });
}

chrome.management.getAll((extensions) => {
  displayExtensions(extensions);
});
