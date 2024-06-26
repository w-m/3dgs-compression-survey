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

// Add event listener for window resize
window.addEventListener('resize', resizePlots);

var groupColors = Plotly.d3.scale.category20().range();

var legendContainer = document.getElementById('legend');
var groupNames = {};

plotData.forEach((plotSet, i) => {
    Object.keys(plotSet).forEach((key, j) => {
        var plotInfo = plotSet[key];
        var points = plotInfo.points;
        var lines = [];

        var groups = {};
        points.forEach(point => {
            if (!groups[point.group]) {
                groups[point.group] = [];
            }
            groups[point.group].push(point);
        });

        var data = [];
        Object.keys(groups).forEach(group => {
            var groupPoints = groups[group];

            if (!groupNames[group]) {
                groupNames[group] = groupColors[groupPoints[0].group_id % groupColors.length];
            }

            data.push({
                x: groupPoints.map(p => p.x),
                y: groupPoints.map(p => p.y),
                mode: 'markers',
                text: groupPoints.map(p => p.label),
                marker: {
                    symbol: 'triangle-up',
                    color: groupColors[groupPoints[0].group_id % groupColors.length],
                    size: 12
                },
                name: group,
                showlegend: false
            });

            if (groupPoints.length > 1) {
                data.push({
                    x: groupPoints.map(p => p.x),
                    y: groupPoints.map(p => p.y),
                    mode: 'lines',
                    line: {
                        color: groupColors[groupPoints[0].group_id % groupColors.length]
                    },
                    showlegend: false,
                    hoverinfo: 'none'
                });
            }
        });

        var layout = {
            title: plotInfo.title,
            xaxis: {
                title: plotInfo.xaxis,
                automargin: true
            },
            yaxis: {
                title: {
                    text: plotInfo.yaxis,
                    // standoff: 5  // only applies to tab 1...?
                },
                automargin: true
            },
            margin: {
                l: 65,
                r: 30,
                b: 70,
                t: 60,
                pad: 0
            },
            showlegend: false
        };

        // Invert y-axis for the third tab
        if (j === 2) {
            layout.yaxis.autorange = 'reversed';
        }
        var config = {
            displayModeBar: false
        };
        Plotly.newPlot(`plot${i}${j + 1}`, data, layout, config);
    });
});

Object.keys(groupNames).forEach(group => {
    var legendItem = document.createElement('div');
    legendItem.className = 'legend-item';

    var colorBox = document.createElement('div');
    colorBox.className = 'legend-color-box';
    colorBox.style.backgroundColor = groupNames[group];

    var labelText = document.createElement('a');
    labelText.href = groupLinks[group];
    labelText.innerText = group;

    legendItem.appendChild(colorBox);
    legendItem.appendChild(labelText);
    legendContainer.appendChild(legendItem);
});

var methodTable = document.getElementById('results');
var methodRows = methodTable.getElementsByClassName('method-name');

Array.from(methodRows).forEach(row => {
    var methodName = row.getAttribute('data-method-name');
    var color = groupNames[methodName];

    if (color) {
        var colorBox = document.createElement('span');
        colorBox.className = 'legend-color-box';
        colorBox.style.backgroundColor = color;

        var colorBoxContainer = row.querySelector('.legend-color-box-container');
        if (colorBoxContainer) {
            colorBoxContainer.insertBefore(colorBox, colorBoxContainer.firstChild);
        }
    }
});