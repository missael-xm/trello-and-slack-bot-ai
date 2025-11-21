// src/dashboard/static/js/analytics.js - CÓDIGO COMPLETO Y CORREGIDO
let charts = {};

async function loadCharts() {
    const period = document.getElementById('periodSelect').value;
    
    try {
        // Cargar datos de las APIs
        const [metrics, categories, priorities, complexity, timeline, skills] = await Promise.all([
            fetch(`/dashboard/api/metrics?days=${period}`).then(r => r.json()),
            fetch(`/dashboard/api/categories?days=${period}`).then(r => r.json()),
            fetch(`/dashboard/api/priorities?days=${period}`).then(r => r.json()),
            fetch(`/dashboard/api/complexity?days=${period}`).then(r => r.json()),
            fetch(`/dashboard/api/timeline?days=${period}`).then(r => r.json()),
            fetch(`/dashboard/api/skills?days=${period}`).then(r => r.json())
        ]);

        // Destruir gráficas existentes para evitar superposición
        Object.values(charts).forEach(chart => {
            if (chart) chart.destroy();
        });

        // Crear nuevas gráficas
        createCategoryChart(categories);
        createPriorityChart(priorities);
        createComplexityChart(complexity);
        createSkillsChart(skills);
        createTimelineChart(timeline);
        updateMetrics(metrics);

    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

function createCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    charts.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(categories).map(key => key.replace('_', ' ')),
            datasets: [{
                data: Object.values(categories),
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                    '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });
}

function createPriorityChart(priorities) {
    const ctx = document.getElementById('priorityChart').getContext('2d');
    
    charts.priority = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(priorities),
            datasets: [{
                label: 'Tareas',
                data: Object.values(priorities),
                backgroundColor: [
                    '#DC2626', '#EA580C', '#D97706', '#059669'
                ],
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}

function createComplexityChart(complexityData) {
    const ctx = document.getElementById('complexityChart').getContext('2d');
    
    charts.complexity = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(complexityData.complexity_distribution).map(key => key.replace('_', ' ')),
            datasets: [{
                data: Object.values(complexityData.complexity_distribution),
                backgroundColor: ['#10B981', '#3B82F6', '#8B5CF6', '#EF4444'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// --- CORRECCIÓN IMPORTANTE AQUÍ ---
function createSkillsChart(skills) {
    const ctx = document.getElementById('skillsChart').getContext('2d');
    
    charts.skills = new Chart(ctx, {
        type: 'bar', // Usar 'bar' en lugar de 'horizontalBar'
        data: {
            labels: Object.keys(skills),
            datasets: [{
                label: 'Frecuencia',
                data: Object.values(skills),
                backgroundColor: '#8B5CF6',
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y', // ESTO HACE QUE SEA HORIZONTAL
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}

function createTimelineChart(timeline) {
    const ctx = document.getElementById('timelineChart').getContext('2d');
    
    const dates = [...new Set(timeline.map(item => item.request_date?.split('T')[0]))].sort();
    const projectsByDate = dates.map(date => 
        timeline.filter(item => item.request_date?.startsWith(date)).length
    );

    charts.timeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Proyectos',
                data: projectsByDate,
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
        }
    });
}

function updateMetrics(metrics) {
    // Actualizar métricas de eficiencia
    const efficiencyHtml = `
        <div class="flex justify-between items-center py-2 border-b border-gray-200">
            <span class="text-gray-600">Tasa de Éxito</span>
            <span class="font-semibold text-green-600">${metrics.success_rate}%</span>
        </div>
        <div class="flex justify-between items-center py-2 border-b border-gray-200">
            <span class="text-gray-600">Promedio Tareas/Proyecto</span>
            <span class="font-semibold text-blue-600">${metrics.average_tasks_per_project}</span>
        </div>
        <div class="flex justify-between items-center py-2">
            <span class="text-gray-600">Promedio Horas/Proyecto</span>
            <span class="font-semibold text-purple-600">${metrics.average_hours_per_project}h</span>
        </div>
    `;
    
    const effElement = document.getElementById('efficiencyMetrics');
    if (effElement) effElement.innerHTML = efficiencyHtml;

    // Actualizar métricas de resumen
    const summaryHtml = `
        <div class="text-center p-4 bg-blue-50 rounded-lg">
            <div class="text-2xl font-bold text-blue-600">${metrics.total_projects}</div>
            <div class="text-sm text-blue-800">Total Proyectos</div>
        </div>
        <div class="text-center p-4 bg-green-50 rounded-lg">
            <div class="text-2xl font-bold text-green-600">${metrics.total_tasks}</div>
            <div class="text-sm text-green-800">Total Tareas</div>
        </div>
        <div class="text-center p-4 bg-purple-50 rounded-lg">
            <div class="text-2xl font-bold text-purple-600">${metrics.total_estimated_hours}</div>
            <div class="text-sm text-purple-800">Horas Estimadas</div>
        </div>
        <div class="text-center p-4 bg-orange-50 rounded-lg">
            <div class="text-2xl font-bold text-orange-600">${metrics.completed_projects}</div>
            <div class="text-sm text-orange-800">Completados</div>
        </div>
    `;
    
    const sumElement = document.getElementById('summaryMetrics');
    if (sumElement) sumElement.innerHTML = summaryHtml;
}

// Cargar inicial
document.addEventListener('DOMContentLoaded', loadCharts);
// Auto-refresh cada 5 minutos
setInterval(loadCharts, 300000);