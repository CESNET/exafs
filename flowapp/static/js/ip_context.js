/*
source https://codepen.io/SitePoint/pen/MYLoWY
*/


/**
 * Variables.
 */
var contextMenuClassName = "context-menu";
var contextMenuItemClassName = "context-menu__item";
var contextMenuLinkClassName = "context-menu__link";
var contextMenuActive = "context-menu--active";

var taskItemClassName = "task";
var taskItemInContext;

var clickCoords;
var clickCoordsX;
var clickCoordsY;

var menu = document.querySelector("#context-menu");
var menuItems = menu.querySelectorAll(".context-menu__item");
var menuState = 0;
var menuWidth;
var menuHeight;
var menuPosition;
var menuPositionX;
var menuPositionY;

var windowWidth;
var windowHeight;

/**
 * Function to check if we clicked inside an element with a particular class
 * name.
 * 
 * @param {Object} e The event
 * @param {String} className The class name to check against
 * @return {Boolean}
 */
 function clickInsideElement( e, className ) {
    var el = e.srcElement || e.target;
    
    if ( el.classList.contains(className) ) {
    return el;
    } else {
    while ( el = el.parentNode ) {
        if ( el.classList && el.classList.contains(className) ) {
        return el;
        }
    }
    }

    return false;
}

/**
 * Get's exact position of event.
 * 
 * @param {Object} e The event passed in
 * @return {Object} Returns the x and y position
 */
function getPosition(e) {
    var posx = 0;
    var posy = 0;

    if (!e) var e = window.event;
    
    if (e.pageX || e.pageY) {
    posx = e.pageX;
    posy = e.pageY;
    } else if (e.clientX || e.clientY) {
    posx = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
    posy = e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
    }

    return {
    x: posx,
    y: posy
    }
}

/**
 * Listens for contextmenu events.
 */
function contextListener() {
    document.addEventListener( "contextmenu", function(e) {
    taskItemInContext = clickInsideElement( e, taskItemClassName );

    if ( taskItemInContext ) {
        e.preventDefault();
        toggleMenuOn();
        positionMenu(e);
    } else {
        taskItemInContext = null;
        toggleMenuOff();
    }
    });
}

/**
 * Listens for click events.
 */
function clickListener() {
    document.addEventListener( "click", function(e) {
    var clickeElIsLink = clickInsideElement( e, contextMenuLinkClassName );

    if ( clickeElIsLink ) {
        e.preventDefault();
        menuItemListener( clickeElIsLink );
    } else {
        var button = e.which || e.button;
        if ( button === 1 ) {
        toggleMenuOff();
        }
    }
    });
}

/**
 * Listens for keyup events.
 */
function keyupListener() {
    window.onkeyup = function(e) {
    if ( e.keyCode === 27 ) {
        toggleMenuOff();
    }
    }
}

/**
 * Window resize event listener
 */
function resizeListener() {
    window.onresize = function(e) {
    toggleMenuOff();
    };
}

/**
 * Turns the custom context menu on.
 */
function toggleMenuOn() {
    if ( menuState !== 1 ) {
    menuState = 1;
    menu.classList.add( contextMenuActive );
    }
}

/**
 * Turns the custom context menu off.
 */
function toggleMenuOff() {
    if ( menuState !== 0 ) {
    menuState = 0;
    menu.classList.remove( contextMenuActive );
    }
}

/**
 * Positions the menu properly.
 * 
 * @param {Object} e The event
 */
function positionMenu(e) {
    clickCoords = getPosition(e);
    clickCoordsX = clickCoords.x;
    clickCoordsY = clickCoords.y;

    menuWidth = menu.offsetWidth + 4;
    menuHeight = menu.offsetHeight + 4;

    windowWidth = window.innerWidth;
    windowHeight = window.innerHeight;

    if ( (windowWidth - clickCoordsX) < menuWidth ) {
    menu.style.left = windowWidth - menuWidth + "px";
    } else {
    menu.style.left = clickCoordsX + "px";
    }

    if ( (windowHeight - clickCoordsY) < menuHeight ) {
    menu.style.top = windowHeight - menuHeight + "px";
    } else {
    menu.style.top = clickCoordsY + "px";
    }
}


/**
 * Initialise our application's code.
 */
 function init() {
    contextListener();
    clickListener();
    keyupListener();
    resizeListener();
}



/**
 * Dispatcher function that performes search action based on data-action attribute
 * 
 * @param {HTMLElement} link The link that was clicked
 */
function menuItemListener( link ) {
    console.log( "Task " + taskItemInContext.innerHTML + " action - " + link.getAttribute("data-action"));
    toggleMenuOff();
    let action = link.getAttribute("data-action"); 
    
    if (action === "whois") {
        window.open('/dashboard/whois/' +  taskItemInContext.innerHTML, '_blank').focus();
    }
    else if (action == "copy") {
        console.log("COPY")
        var r = document.createRange();
        r.selectNode(taskItemInContext);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(r);
        document.execCommand('copy');
        window.getSelection().removeAllRanges();
    }
    
}


/**
 * Run the app.
 */
document.addEventListener('DOMContentLoaded', init);
