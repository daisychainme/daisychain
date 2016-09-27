(function(){
    "use strict";

    function createOverlay(node) {
        var rect = node.getBoundingClientRect();
        var div = document.createElement("div");
        div.classList.add("form-control");
        div.classList.add("recipe--mapping_overlay");
        div.style.width = rect.width + "px";
        node.parentElement.insertBefore(div, node);
    };

    function createBubble(text) {
        var bubble = document.createElement("span");
        bubble.classList.add("recipe--mapping_bubble");
        bubble.textContent = text;
        return bubble;
    };

    function createBubbleSelection(wordList) {
        var node = document.createElement("div");
        node.classList.add("recipe--mapping_bubble_list");
        wordList.forEach(function(value) {
            var bubble = createBubble(value);
            bubble.style.margin = ".25em";
            bubble.style.float = "left";
            node.appendChild(bubble);
            enable_drag(bubble);
        });
        var clearLeft = document.createElement("div");
        clearLeft.style.clear = "left";
        node.appendChild(clearLeft);
        return node;
    }

    function blur(input, overlay) {
        input.style.color = "transparent";
        var bubbleValues = input.getAttribute("data-bubble-input").trim().split(" ");
        var overlayText = input.value.replace(/ /g, '&nbsp;');
        overlayText = overlayText.replace(/%(.*?)%/g, function(match, keyword) {
            if(bubbleValues.indexOf(keyword) > -1) {
                return createBubble(keyword).outerHTML;
            } else {
                return match;
            }
        });
        overlay.innerHTML = overlayText;
    };

    function blurEvent(e) {
        blur(e.target, e.target.previousElementSibling);
    };

    function focusEvent(e) {
        e.target.style.color = "";
        e.target.previousElementSibling.textContent = "";
    };

    function dropEvent(e) {
        window.setTimeout(function() {
            blur(e.target, e.target.previousElementSibling);
        }, 0);
    };

    function enable_bubbles(node) {
        createOverlay(node);
        if(node != document.activeElement) {
            blurEvent({target: node});
        }

        node.addEventListener("blur", blurEvent);
        node.addEventListener("focus", focusEvent);
        node.addEventListener("drop", dropEvent);

        var bubbleValues = node.getAttribute("data-bubble-input").trim().split(" ");
        node.parentElement.insertBefore(
                createBubbleSelection(bubbleValues),
                node.nextElementSibling);
    };

    function dragStartEvent(e) {
        e.dataTransfer.setData("text", "%" + e.target.textContent + "%");
    };

    function enable_drag(node) {
        node.setAttribute("draggable", "true");
        node.addEventListener("dragstart", dragStartEvent);
    };

    var nodes = document.querySelectorAll("[data-bubble-input]");
    for(var x = nodes.length-1; x > -1; x--) {
        enable_bubbles(nodes[x]);
    }

})();

