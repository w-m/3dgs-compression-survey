function showTab(tabId, buttonId) {
    var container = document.getElementById(tabId).parentElement;
    container.querySelectorAll('.tab').forEach(tab => tab.classList.remove('tab-active'));
    container.querySelectorAll('.tab-buttons button').forEach(button => button.classList.remove('active'));
    document.getElementById(tabId).classList.add('tab-active');
    document.getElementById(buttonId).classList.add('active');
    
    // Force a resize after loading tab to avoid resize artifacts
    var plotContent = document.getElementById(tabId).querySelector('.plot-content');
    Plotly.Plots.resize(plotContent);
    Plotly.relayout(plotContent, {
        width: plotContent.clientWidth,
        height: plotContent.clientHeight
    });
}

// Function to resize all plots
function resizePlots() {
    document.querySelectorAll('.plot-content').forEach(plotContent => {
        Plotly.Plots.resize(plotContent);
        Plotly.relayout(plotContent, {
            width: plotContent.clientWidth,
            height: plotContent.clientHeight
        });
    });
}

var legendContainer = document.getElementById('legend');

function drawPlots(plotData, allowedKeys, allowedDatasets) {
    plotData.forEach((plotSet, i) => {
        if (!allowedDatasets.includes(i)) return;

        Object.keys(plotSet).forEach((key, j) => {
            if (!allowedKeys.includes(key)) return;

            const plotInfo = plotSet[key];
            const groupData = plotInfo.groupData;

            const data = [];
            for (const [group, { x, x2, y, text }] of Object.entries(groupData)) {
                const color = groupColors[group];
                const visible = checkboxStates[group];
                const xValues = plotOption === 'size' ? x : x2;

                // if all xvalues are nan continue
                if (xValues.every(v => isNaN(v))) continue
                
                data.push({
                    x: xValues,
                    y,
                    mode: 'markers',
                    text,
                    marker: {
                        symbol: 'triangle-up',
                        color,
                        size: 12
                    },
                    name: group,
                    showlegend: false,
                    visible
                });

                if (xValues.length > 1) {
                    data.push({
                        x: xValues,
                        y,
                        mode: 'lines',
                        line: { color },
                        showlegend: false,
                        hoverinfo: 'none',
                        visible
                    });
                }
            }

            const xlabel = plotOption === 'size' ? 'Size (MB)' : '#Gaussians';

            const layout = {
                title: plotInfo.title,
                xaxis: {
                    title: xlabel, //plotInfo.xaxis,
                    automargin: true,
                    zeroline: false
                },
                yaxis: {
                    title: plotInfo.yaxis,
                    automargin: true,
                    autorange: j === 2 ? 'reversed' : true
                },
                margin: { l: 65, r: 30, b: 70, t: 60, pad: 0 },
                shapes: plotInfo.lineHeight !== null ? [{
                    type: 'line',
                    x0: 0,
                    x1: 1,
                    y0: plotInfo.lineHeight,
                    y1: plotInfo.lineHeight,
                    xref: 'paper',
                    yref: 'y',
                    line: { color: 'rgba(100, 100, 100, 0.75)', width: 2, dash: 'dash' }
                }] : [],
                showlegend: false
            };

            Plotly.newPlot(`plot${i}${j + 1}`, data, layout, { displayModeBar: false });
        });
    });
}


function drawLegend() {

    // Add the legend item for 3DGS with a dashed line
    var legendItem3DGS = document.createElement('div');
    legendItem3DGS.className = 'legend-item';

    var dashedLine = document.createElement('div');
    dashedLine.style.width = '20px';
    dashedLine.style.height = '0';
    dashedLine.style.borderTop = '2px dashed rgba(100, 100, 100, 0.75)';
    dashedLine.style.marginRight = '5px';

    var labelText3DGS = document.createElement('p');
    labelText3DGS.innerText = '3DGS-30K';
    labelText3DGS.style.color = '#333333';

    legendItem3DGS.appendChild(dashedLine);
    legendItem3DGS.appendChild(labelText3DGS);
    legendContainer.appendChild(legendItem3DGS);

    // Add rest of legend items

    Object.keys(groupColors).forEach(group => {
        var legendItem = document.createElement('div');
        legendItem.className = 'legend-item';

        var checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = checkboxStates[group];
        checkbox.dataset.group = group;
        checkbox.style.marginLeft = '5px';
        checkbox.addEventListener('change', updatePlotVisibility);

        var colorBox = document.createElement('div');
        colorBox.className = 'legend-color-box';
        colorBox.style.backgroundColor = groupColors[group];

        var labelText = document.createElement('a');
        labelText.href = groupLinks[group];
        labelText.innerText = group;

        legendItem.appendChild(colorBox);
        legendItem.appendChild(labelText);
        legendItem.appendChild(checkbox);
        legendContainer.appendChild(legendItem);
    });
}

function updatePlotVisibility(event) {
    var group = event.target.dataset.group;
    var visible = event.target.checked;

    document.querySelectorAll('.plot-content').forEach(plotContent => {
        plotContent.data.forEach((trace, index) => {
            if (trace.name === group || (trace.line && trace.line.color === groupColors[group])) {
                Plotly.restyle(plotContent, { visible: visible }, [index]);
            }
        });
    });
}

function updateRanks() {    
    let selected_string = '';

    // Process column-toggle checkboxes
    $('.column-toggle').slice(0, 4).each(function() {
        if ($(this).is(':checked')) {
            selected_string += '1';
        }
        else {
            selected_string += '0';
        }
    });

    // Process column-toggle-datasets checkboxes
    $('.column-toggle-datasets').each(function() {
        if ($(this).is(':checked')) {
            selected_string += '1';
        }
        else {
            selected_string += '0';
        }
    });

    if (selected_string.startsWith('0000') || selected_string.endsWith('0000')) {
        selected_string = '11111111';
    }

    const [newrank, classes] = rankCombinations[selected_string];
    for (var i = 0; i < table.columns(1).data()[0].length; i++) {
        table.cell(i, 1).data(newrank[i]);

        $(table.cell(i, 1).node()).removeClass();
        if (classes[i] != "") {
            $(table.cell(i, 1).node()).addClass(classes[i]);
        }

        $(table.cell(i, 1).node()).addClass('has-text-right');
    
    }
    // sort the table
    table.order([1, 'asc']).draw();

    document.getElementById('formula').innerHTML = katex.renderToString(metricFormulas[selected_string.slice(0, 4)])
}

const switchInput = document.getElementById('switchInput');
let plotOption = 'size';  

window.addEventListener('load', () => {
    const plots = ["plot1", "plot2", "plot3"];
    const shortDelay = 20; // ms to wait between plot drawings

    async function drawPlotsSequentially() {
        for (const plot of plots) {
            for (let i = 0; i < 4; i += 1) {
                await new Promise(resolve => {
                    requestAnimationFrame(() => {
                        drawPlots(plotData, [plot], [i]);
                        setTimeout(resolve, shortDelay);
                    });
                });
            }
        }
    }

    drawLegend();

    drawPlotsSequentially();

    window.addEventListener('resize', resizePlots);
  
    switchInput.addEventListener('change', function() {
        if (this.checked) {
            plotOption = 'gaussians';
        } else {
            plotOption = 'size';
        }
        drawPlotsSequentially();
    });

});

