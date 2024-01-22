const pointerScroll = (elem) => {
    let isDrag = false;

    const dragStart = () => (isDrag = true);
    const dragEnd = () => (isDrag = false);
    const drag = (ev) =>
        isDrag && (elem.scrollLeft -= ev.movementX) && (elem.scrollTop -= ev.movementY);

    elem.addEventListener("pointerdown", dragStart);
    addEventListener("pointerup", dragEnd);
    addEventListener("pointermove", drag);
};

document.querySelectorAll(".bracketContent").forEach(pointerScroll);
