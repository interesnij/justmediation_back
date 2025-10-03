function on(elSelector,eventName,selector,fn) {var element = document.querySelector(elSelector);element.addEventListener(eventName, function(event) {var possibleTargets = element.querySelectorAll(selector);var target = event.target;for (var i = 0, l = possibleTargets.length; i < l; i++) {var el = target;var p = possibleTargets[i];while(el && el !== element) {if (el === p) {return fn.call(p, event);}el = el.parentNode;}}});};
function elementInViewport(el){var bounds = el.getBoundingClientRect();return ((bounds.top + bounds.height > 0) && (window.innerHeight - bounds.top > 0));}

function paginate(block) {
    var link_3 = window.XMLHttpRequest ? new XMLHttpRequest() : new ActiveXObject('Microsoft.XMLHTTP');
    link_3.open('GET', location.protocol + "//" + location.host + block.getAttribute("data-link"), true);
    link_3.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

    link_3.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {

            var elem = document.createElement('span');
            elem.innerHTML = link_3.responseText;
            block.parentElement.insertAdjacentHTML('beforeend', elem.querySelector(".loading_tbody").innerHTML)
            block.remove()
        }
    }
    link_3.send();
};

function scrolled(_block) {
    onscroll = function() {
        try {
            box = _block.querySelector('.next_page_list');
            if (box && box.classList.contains("next_page_list")) {
                inViewport = elementInViewport(box);
                if (inViewport) {
                    box.classList.remove("next_page_list");
                    paginate(box);
                }
            };
        } catch {return}
    }
};

scrolled(document.body);