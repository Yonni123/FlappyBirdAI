function init() {
    ggbApplet.evalCommand("a=-1");

    ggbApplet.evalCommand('h_s = Slider[0, 100, 0.5, 1, 100, false, true, true, false]');
    ggbApplet.evalCommand('k_s = Slider[0, 100, 0.5, 1, 100, false, true, true, false]');
    ggbApplet.evalCommand("f(x) = a*(x-h_s)^2 + k_s");

    ggbApplet.evalCommand('h_e = Slider[0, 100, 0.5, 1, 100, false, true, true, false]');
    ggbApplet.evalCommand('k_e = Slider[0, 100, 0.5, 1, 100, false, true, true, false]');
    ggbApplet.evalCommand("g(x) = a*(x-h_e)^2 + k_e");

    ["h_s", "k_s", "h_e", "k_e"].forEach(name => {
        ggbApplet.setAnimating(name, false);
    });
    ggbApplet.stopAnimation();

    ggbApplet.evalCommand("t = 1");   // time-to-peak
    ggbApplet.evalCommand(`Point_ttp_s = (h_s - t, f(h_s - t))`);
    ggbApplet.evalCommand(`Point_ttp_e = (h_e - t, g(h_e - t))`);
    ggbApplet.setLabelVisible("Point_ttp_s", false);
    ggbApplet.setLabelVisible("Point_ttp_e", false);
}
init();

function generate_fit() {
    const a = ggbApplet.getValue("a");
    const hs = ggbApplet.getValue("h_s");
    const he = ggbApplet.getValue("h_e");
    const ks = ggbApplet.getValue("k_s");
    const ke = ggbApplet.getValue("k_e");
    const ttp = ggbApplet.getValue("t");

    const H = he - hs;
    const S_t = (ke - ks)/a + 2*ttp*H;

    // Compute minimal feasible n
    let n = Math.ceil(H*H / S_t);
    if(n < 2) n = 2;

    const disc = (n-1)*(n*S_t - H*H);
    if(disc < 0){
        console.warn("No real solution: increase n!");
        return;
    }

    const sqrtDisc = Math.sqrt(disc);
    const d_step = (H*(n-1) - sqrtDisc) / (n*(n-1)); // minus branch
    const d_last = H - (n-1)*d_step;

    // generate parabolas
    let h_prev = hs;
    let k_prev = ks;

    for(let i=1;i<=(n-1);i++){
        const d_i = i<n ? d_step : d_last;
        const h_i = h_prev + d_i;
        const k_i = k_prev + a*(d_i*d_i - 2*ttp*d_i);

        ggbApplet.evalCommand(`p_${i}(x) = ${a}*(x - ${h_i})^2 + ${k_i}`);

        // plot ttp point (optional)
        const ttp_x = h_i - ttp;
        const ttp_y = a*ttp*ttp + k_i;
        ggbApplet.evalCommand(`Point_ttp_${i} = (${ttp_x}, ${ttp_y})`);
        ggbApplet.setLabelVisible(`Point_ttp_${i}`, false);

        h_prev = h_i;
        k_prev = k_i;
    }
}
generate_fit();

function clear_fit() {
    const n = 100000;   
    for (let i = 1; i < n; i++) {
        if (!ggbApplet.exists(`p_${i}`)) break;
        ggbApplet.deleteObject(`p_${i}`);
        ggbApplet.deleteObject(`Point_ttp_${i}`);
    }
}
clear_fit();

// === Create three buttons ===
ggbApplet.evalCommand('btn_init = Button("Initialize")');
ggbApplet.setCoords("btn_init", 2, 8);

ggbApplet.evalCommand('btn_generate = Button("Generate Fit")');
ggbApplet.setCoords("btn_generate", 2, 7);

ggbApplet.evalCommand('btn_clear = Button("Clear Fit")');
ggbApplet.setCoords("btn_clear", 2, 6);

ggbApplet.deleteObject("button1");
