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

                let symbol = 'triangle-up'
                if (group in densificationMethods){
                    symbol = "circle"
                }
                
                data.push({
                    x: xValues,
                    y,
                    mode: 'markers',
                    text,
                    marker: {
                        symbol: symbol,
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
        if (group === "3DGS") {
            return;
        }
        var legendItem = document.createElement('div');
        legendItem.className = 'legend-item';

        var checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = checkboxStates[group];
        checkbox.dataset.group = group;
        checkbox.style.marginLeft = '5px';
        checkbox.addEventListener('change', updatePlotVisibility);

        var colorBox = document.createElement('div');
        if (group in densificationMethods){
            colorBox.className = 'legend-color-box densification';
        }else{
            colorBox.className = 'legend-color-box';
        }
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
    checkboxStates[group] = !checkboxStates[group]

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

    const category = switchInputCD.checked ? 'densification' : 'compression';
    const both = $('.row-toggle-c').is(':checked') && $('.row-toggle-d').is(':checked');

    // Process column-toggle checkboxes
    $('.column-toggle').slice(0, 5).each(function() {
        if ($(this).is(':checked')) {
            selected_string += '1';
        }
        else {
            selected_string += '0';
        }
    });
    // include the 3 quality metrics + size for compressin / + #Gaussians for densification
    if (category === 'densification') {
        selected_string = selected_string.slice(0, 3) + selected_string.slice(4);
    } else if (category === 'compression') {
        selected_string = selected_string.slice(0, 4);
    }

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

    let rank_category;
    // Extend category with "_all" if both are checked
    if (both) {
        rank_category = category + '_all';
    } else {
        rank_category = category;
    }

    if (category === 'densification') {
        selected_string = selected_string.slice(0,6)
    }

    const [newrank, classes] = rankCombinations[rank_category][selected_string];
    let ii = 0
    for (var i = 0; i < table.columns(1).data()[0].length; i++) {
        if (!both && methodCategories[i] != category.slice(0,1) && methodCategories[i] != "3") { // ranks only apply to selected methods with correct category, always use 3 (3DGS)
            continue;
        }
        table.cell(i, 1).data(newrank[ii]);

        $(table.cell(i, 1).node()).removeClass();
        if (classes[ii] != "") {
            $(table.cell(i, 1).node()).addClass(classes[ii]);
        }

        $(table.cell(i, 1).node()).addClass('has-text-right');
        ii++;
    
    }
    // sort the table
    table.order([1, 'asc']).draw();

    document.getElementById('formula').innerHTML = katex.renderToString(metricFormulas[category][selected_string.slice(0, 4)])
}

function updateRowVisibility() {
    var compression = $('.row-toggle-c').is(':checked');
    var densification = $('.row-toggle-d').is(':checked');

    // Iterate over all rows in the DataTable
    table.rows().every(function(rowIdx) {
        var categoryValue = methodCategories[rowIdx]; // Access category value for this row
        var shouldShowRow = true;

        if (categoryValue.trim() === 'd' && !densification) {
            shouldShowRow = false; // Hide rows with category 'd' if densification is unchecked
        } else if (categoryValue.trim() === 'c' && !compression) {
            shouldShowRow = false; // Hide rows with category 'c' if compression is unchecked
        }

        var rowNode = this.node();
        $(rowNode).css('display', shouldShowRow ? '' : 'none');
    });

    // Adjust column sizing and redraw the table for correct layout
    table.columns.adjust().draw();
}

const switchInput = document.getElementById('switchInput');
const switchInputCD = document.getElementById('switchInputCD');
let plotOption = 'size';  

updateRowVisibility();

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

    document.getElementById('formula').innerHTML = katex.renderToString(metricFormulas["compression"]["1111"])
  
    switchInput.addEventListener('change', function() {
        if (this.checked) {
            plotOption = 'gaussians';
        } else {
            plotOption = 'size';
        }
        drawPlotsSequentially();
    });

    switchInputCD.addEventListener('change', function() {
        if (this.checked) { // densifictaion
            $('.row-toggle-c').prop('checked', false);
            $('.row-toggle-d').prop('checked', true);

            // Show first 2 datasets (t&t and mip)
            $('.column-toggle-datasets').eq(0).prop('checked', true);
            $('.column-toggle-datasets').eq(1).prop('checked', true);

            // hide last 2
            $('.column-toggle-datasets').eq(2).prop('checked', false);
            $('.column-toggle-datasets').eq(3).prop('checked', false);

            // show psnr, ssim, lpips, size
            $('.column-toggle').prop('checked', false);
            $('.column-toggle').slice(0, 3).prop('checked', true);
            $('.column-toggle').eq(4).prop('checked', true);

        } else { // compression
            $('.row-toggle-c').prop('checked', true);
            $('.row-toggle-d').prop('checked', false);

            //show all datasets
            $('.column-toggle-datasets').prop('checked', true);

            // show psnr, ssim, lpips, size
            $('.column-toggle').prop('checked', false);
            $('.column-toggle').slice(0, 4).prop('checked', true);
        }
        updateRowVisibility()
        updateColumnVisibility()
        updateRanks()
    });

    $('.row-toggle-c, .row-toggle-d').on('change', updateRowVisibility);

});

