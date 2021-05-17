let timer = setInterval(function() {
    let names = document.getElementsByClassName('grid-accounts-user');

    for (let i = 0; i < names.length; i++) {
        clearInterval(timer);
        names[i].addEventListener('mousemove', displayProfilePicture);
        names[i].addEventListener('mouseleave', hideProfilePicture);
    }
}, 100);

function displayProfilePicture(event) {
    let profilePictureUrl = null;

    for (let i = 0; i < users.length; i++) {
        if (users[i]['lastName'] + ', ' + users[i]['firstName'] === event.target.innerText) {
            profilePictureUrl = users[i]['profilePictureUrl'];
        }
    }

    if (profilePictureUrl != null) {
        const cursorX = (event.pageX || event.clientX);
        const cursorY = (event.pageY || event.clientY);
        let containerProfilePicture = document.getElementById('container-profile-picture');
        containerProfilePicture.style.left = cursorX + 'px';
        containerProfilePicture.style.top = cursorY + 'px';
        containerProfilePicture.style.backgroundImage = 'url(' + profilePictureUrl + ')';
        containerProfilePicture.style.opacity = '1';
    }
}

function hideProfilePicture(event) {
    let containerProfilePicture = document.getElementById('container-profile-picture');
    containerProfilePicture.style.opacity = '0';
}
