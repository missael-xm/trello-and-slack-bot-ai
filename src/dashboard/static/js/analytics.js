// src/dashboard/static/js/analytics.js
let charts = {};

async function loadCharts() {
    const period = document.getElementById('periodSelect').value;
    try {
        const fetchSafe = (url) => fetch(url).then(r => r.json()).catch(() => ({}));
        
        const [metrics, categories, priorities, complexity, timeline, skills, teamMetrics] = await Promise.all([
            fetchSafe(`/dashboard/api/metrics?days=${period}`),
            fetchSafe(`/dashboard/api/categories?days=${period}`),
            fetchSafe(`/dashboard/api/priorities?days=${period}`),
            fetchSafe(`/dashboard/api/complexity?days=${period}`),
            fetchSafe(`/dashboard/api/timeline?days=${period}`),
            fetchSafe(`/dashboard/api/skills?days=${period}`),
            fetchSafe(`/dashboard/api/team-metrics`)
        ]);

        Object.values(charts).forEach(c => { if(c) c.destroy(); });

        createCategoryChart(categories);
        createPriorityChart(priorities);
        createComplexityChart(complexity);
        createSkillsChart(skills);
        createTimelineChart(Array.isArray(timeline) ? timeline : []);
        
        updateMetrics(metrics);
        // Si existe función de team summary en esta página, llamarla
        if (typeof updateTeamSummary === 'function' && teamMetrics) {
            updateTeamSummary(teamMetrics);
        }

    } catch (error) { console.error('Error loading charts:', error); }
}

function createCategoryChart(data) {
    const ctx = document.getElementById('categoryChart');
    if(!ctx) return;
    
    charts.category = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: Object.keys(data || {}),
            datasets: [{
                data: Object.values(data || {}),
                backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // CRÍTICO para evitar estiramiento
            plugins: { legend: { position: 'right' } }
        }
    });
}

function createPriorityChart(data) {
    const ctx = document.getElementById('priorityChart');
    if(!ctx) return;
    
    const labels = ['Alta', 'Media', 'Baja'];
    const values = labels.map(l => (data || {})[l] || 0);
    
    charts.priority = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Tareas',
                data: values,
                backgroundColor: ['#EF4444', '#F59E0B', '#10B981'],
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // CRÍTICO
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

function createComplexityChart(data) {
    const ctx = document.getElementById('complexityChart');
    if(!ctx) return;
    
    const dist = (data || {}).complexity_distribution || {};
    
    charts.complexity = new Chart(ctx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: Object.keys(dist),
            datasets: [{
                data: Object.values(dist),
                backgroundColor: ['#10B981', '#3B82F6', '#8B5CF6', '#EF4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // CRÍTICO
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

function createSkillsChart(skills) {
    const ctx = document.getElementById('skillsChart');
    if(!ctx) return;
    
    const sorted = Object.entries(skills || {}).sort((a,b)=>b[1]-a[1]).slice(0,8);
    
    charts.skills = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: sorted.map(s=>s[0]),
            datasets: [{
                label: 'Frecuencia',
                data: sorted.map(s=>s[1]),
                backgroundColor: '#8B5CF6',
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false, // CRÍTICO
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

function createTimelineChart(timeline) {
    const ctx = document.getElementById('timelineChart');
    if(!ctx) return;
    
    const dates = [...new Set(timeline.map(t => t.request_date?.split('T')[0]))].sort();
    const counts = dates.map(d => timeline.filter(t => t.request_date?.startsWith(d)).length);
    
    charts.timeline = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Proyectos',
                data: counts,
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // CRÍTICO
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

function updateMetrics(m) {
    // Actualizar resumen de eficiencia (lado izquierdo)
    const effEl = document.getElementById('efficiencyMetrics');
    if(effEl) {
        effEl.innerHTML = `
            <div class="flex justify-between items-center py-2 border-b border-gray-200">
                <span class="text-gray-600">Tasa de Éxito</span>
                <span class="font-semibold text-green-600">${m.success_rate||0}%</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-gray-200">
                <span class="text-gray-600">Tareas/Proy</span>
                <span class="font-semibold text-blue-600">${m.average_tasks_per_project||0}</span>
            </div>
            <div class="flex justify-between items-center py-2">
                <span class="text-gray-600">Horas/Proy</span>
                <span class="font-semibold text-purple-600">${m.average_hours_per_project||0}h</span>
            </div>`;
    }

    // Actualizar tarjetas de resumen (lado derecho)
    const sumEl = document.getElementById('summaryMetrics');
    if(sumEl) {
        sumEl.innerHTML = `
            <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                <div class="text-2xl font-bold text-blue-600">${m.total_projects||0}</div>
                <div class="text-xs text-blue-800 font-medium mt-1">Proyectos</div>
            </div>
            <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                <div class="text-2xl font-bold text-green-600">${m.total_tasks||0}</div>
                <div class="text-xs text-green-800 font-medium mt-1">Tareas</div>
            </div>
            <div class="text-center p-4 bg-purple-50 rounded-lg border border-purple-100">
                <div class="text-2xl font-bold text-purple-600">${m.total_estimated_hours||0}h</div>
                <div class="text-xs text-purple-800 font-medium mt-1">Horas</div>
            </div>
            <div class="text-center p-4 bg-orange-50 rounded-lg border border-orange-100">
                <div class="text-2xl font-bold text-orange-600">${m.completed_projects||0}</div>
                <div class="text-xs text-orange-800 font-medium mt-1">Completados</div>
            </div>`;
    }
}

document.addEventListener('DOMContentLoaded', loadCharts);