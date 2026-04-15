async function apiPost(url, payload) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    return response.json();
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function formatPercent(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return '-';
    }
    return `${(Number(value) * 100).toFixed(2)}%`;
}

function formatMetric(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return '-';
    }
    return Number(value).toFixed(4);
}

function renderPieChart(domId, data, title) {
    const container = document.getElementById(domId);
    if (!container || typeof echarts === 'undefined') {
        return;
    }
    const chart = echarts.init(container);
    chart.setOption({
        title: {text: title, left: 'center', top: 4, textStyle: {fontSize: 15}},
        tooltip: {trigger: 'item'},
        legend: {bottom: 0, left: 'center'},
        series: [
            {
                name: title,
                type: 'pie',
                radius: ['42%', '68%'],
                center: ['50%', '48%'],
                data: data,
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.2)'
                    }
                }
            }
        ]
    });
    window.addEventListener('resize', () => chart.resize());
}
