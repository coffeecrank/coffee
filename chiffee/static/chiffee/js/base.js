window.onload = function () {
    displayTime();
    repositionContent();
    adjustDropdown();

    const body = document.getElementsByTagName('body')[0];
    body.style.visibility = 'visible';
};

function displayTime() {
    const now = new Date();
    const clock = document.getElementById('clock');
    clock.innerHTML = ('0' + now.getHours()).slice(-2) + ':' + ('0' + now.getMinutes()).slice(-2);
    clock.dateTime = now.toISOString();

    setTimeout(displayTime, 1000);
}

function repositionContent() {
    const headerHeight = document.getElementById('header').offsetHeight;
    const content = document.getElementById('content');
    content.style.marginTop = (headerHeight + 20) + 'px';
    content.style.height = 'calc(100vh - ' + (headerHeight + 40) + 'px)';
}

function adjustDropdown() {
    const dropdown = document.getElementById('dropdown');

    if (dropdown == null) {
        return;
    }

    const dropdownClone = dropdown.cloneNode(true);

    const nav = document.getElementById('nav');
    nav.appendChild(dropdownClone);

    const dropdownCloneDiv = dropdownClone.getElementsByTagName('div')[0];
    dropdownCloneDiv.style.display = 'flex';
    dropdownCloneDiv.style.flexDirection = 'column';
    const dropdownCloneDivWidth = dropdownCloneDiv.offsetWidth;

    nav.removeChild(dropdownClone);
    dropdown.style.minWidth = dropdownCloneDivWidth + 'px';
    dropdown.getElementsByTagName('div')[0].style.top = (dropdown.offsetHeight - 1) + 'px';

    for (let i = 0; i < nav.childElementCount; i++) {
        nav.children[i].style.minWidth = dropdownCloneDivWidth + 'px';
    }
}
