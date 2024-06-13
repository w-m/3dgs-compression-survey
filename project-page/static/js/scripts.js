function showTab(tabId, buttonId) {
    var container = document.getElementById(tabId).parentElement;
    container.querySelectorAll('.tab').forEach(tab => tab.classList.remove('tab-active'));
    container.querySelectorAll('.tab-buttons button').forEach(button => button.classList.remove('active'));
    document.getElementById(tabId).classList.add('tab-active');
    document.getElementById(buttonId).classList.add('active');
    Plotly.Plots.resize(document.getElementById(tabId).querySelector('.plot-content'));
}

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
                b: 10,
                t: 60,
                pad: 0
            },
            showlegend: false
        };
        
        Plotly.newPlot(`plot${i}${j + 1}`, data, layout);
    });
});

Object.keys(groupNames).forEach(group => {
    var legendItem = document.createElement('div');
    legendItem.className = 'legend-item';

    var colorBox = document.createElement('div');
    colorBox.className = 'legend-color-box';
    colorBox.style.backgroundColor = groupNames[group];

    var labelText = document.createElement('span');
    labelText.innerText = group;

    legendItem.appendChild(colorBox);
    legendItem.appendChild(labelText);
    legendContainer.appendChild(legendItem);
});