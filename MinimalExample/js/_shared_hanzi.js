console.log("[_shared_hanzi.js] FILE PARSED");

// =====================================================
//  Load JSON override
// =====================================================
if (typeof HanziWriter === "undefined") {
    console.error("[_shared_hanzi.js] ERROR: HanziWriter NOT FOUND");
} else {
    HanziWriter.loadCharacterData = function(char) {
        return fetch(char + ".json").then(r => r.json());
    };
}

let _writers = [];

// =====================================================
//  Replay animation
// =====================================================
function replayAnimation() {
    console.log("[_shared_hanzi.js] replayAnimation");

    _writers.forEach((writer, i) => {
        setTimeout(() => writer.animateCharacter(), i * 150);
    });
}

// =====================================================
//  Build the writers for THIS CARD
// =====================================================
window.initHanziWriter = function(chars) {
    console.log("[_shared_hanzi.js] initHanziWriter:", chars);

    const container = document.getElementById("writer-container");
    if (!container) {
        console.error("[_shared_hanzi.js] writer-container missing");
        return;
    }

    container.innerHTML = "";
    _writers = [];

    const charList = [...chars];
    const count = charList.length;

    // ================ RESPONSIVE SIZE ================
    const screenWidth = Math.min(window.innerWidth, document.body.clientWidth) - 20;

    const rawSize = Math.floor((screenWidth - (count - 1) * 12) / count);

    // sécurité : taille min + max raisonnables
    const size = Math.max(60, Math.min(rawSize, 140));

    console.log("[_shared_hanzi.js] Computed size per char:", size);

    // =================================================
    //  Create writer blocks
    // =================================================
    charList.forEach((char, index) => {
        const div = document.createElement("div");
        div.id = "writer-" + index;
        div.style.width = size + "px";
        div.style.height = size + "px";
        div.style.border = "2px solid #555";
        div.style.borderRadius = "8px";
        div.style.background = "#222";
        div.style.display = "flex";
        div.style.justifyContent = "center";
        div.style.alignItems = "center";
        div.style.margin = "5px";

        container.appendChild(div);

        const writer = new HanziWriter(div.id, {
            width: size,
            height: size,
            padding: 10,
            showCharacter: true,
            showOutline: true,
            strokeAnimationSpeed: 3,
            delayBetweenStrokes: 50
        });

        writer.setCharacter(char);
        _writers.push(writer);
    });

    // initial animation
    setTimeout(replayAnimation, 150);

    // attach the button
    attachReplayButtonHandler();
};

// =====================================================
//  Connect the replay button
// =====================================================
function attachReplayButtonHandler() {
    const btn = document.getElementById("replay-btn");
    if (!btn) return;

    console.log("[_shared_hanzi.js] Replay button attached");

    btn.onclick = replayAnimation;

    btn.onmouseover = () => btn.style.background = "#5a63ff";
    btn.onmouseout  = () => btn.style.background = "#444cf7";
}
