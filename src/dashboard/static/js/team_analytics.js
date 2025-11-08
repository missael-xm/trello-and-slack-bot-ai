// src/dashboard/static/js/team_analytics.js
let teamCharts = {};

async function loadTeamMetrics() {
    const period = document.getElementById('periodSelect').value;
    
    try {
        // Cargar datos de las APIs
        const [teamMetrics, memberMetrics] = await Promise.all([
            fetch(`/dashboard/api/team-metrics?days=${period}`).then(r => r.json()),
            fetch(`/dashboard/api/member-metrics?days=${period}`).then(r => r.json())
        ]);

        // Actualizar métricas principales
        updateMainMetrics(teamMetrics);
        
        // Actualizar tabla de miembros
        updateMembersTable(memberMetrics.members);
        
        // Crear/actualizar gráficas
        createWorkloadChart(memberMetrics.members);
        createSkillsChart(teamMetrics.skill_coverage);
        createSkillsDistribution(memberMetrics.members);

    } catch (error) {
        console.error('Error loading team metrics:', error);
        alert('Error al cargar las métricas del equipo: ' + error.message);
    }
}

function updateMainMetrics(metrics) {
    document.getElementById('totalMembers').textContent = metrics.total_members;
    document.getElementById('availableMembers').textContent = `${metrics.available_members} disponibles`;
    document.getElementById('totalTasks').textContent = metrics.total_tasks_assigned;
    document.getElementById('completedTasks').textContent = `${metrics.total_tasks_completed} completadas`;
    document.getElementById('completionRate').textContent = `${metrics.completion_rate.toFixed(1)}%`;
    document.getElementById('successRate').textContent = `Rendimiento: ${metrics.completion_rate >= 80 ? 'Excelente' : metrics.completion_rate >= 60 ? 'Bueno' : 'Necesita mejora'}`;
    document.getElementById('busyMembers').textContent = metrics.busy_members.length;
}

function updateMembersTable(members) {
    const tableBody = document.getElementById('teamMembersTable');
    
    if (!members || members.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-4 text-center text-gray-500">
                    No hay datos de miembros del equipo
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = members.map(member => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-user text-blue-600"></i>
                    </div>
                    <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">${member.name}</div>
                        <div class="text-sm text-gray-500">${member.slack_id}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">${member.current_tasks}</div>
                <div class="text-xs text-gray-500">de capacidad</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    ${member.completed_tasks} tareas
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-${member.utilization > 80 ? 'red' : member.utilization > 60 ? 'yellow' : 'green'}-600 h-2 rounded-full" 
                         style="width: ${member.utilization}%"></div>
                </div>
                <div class="text-xs text-gray-600 mt-1">${member.utilization.toFixed(1)}%</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="text-sm font-medium ${member.success_rate >= 90 ? 'text-green-600' : member.success_rate >= 75 ? 'text-yellow-600' : 'text-red-600'}">
                    ${member.success_rate.toFixed(1)}%
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${member.avg_completion_time ? member.avg_completion_time.toFixed(1) + 'h' : 'N/A'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${member.available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                    ${member.available ? 'Disponible' : 'Ocupado'}
                </span>
            </td>
        </tr>
    `).join('');
}

function createWorkloadChart(members) {
    const ctx = document.getElementById('workloadChart').getContext('2d');
    
    // Destruir gráfica existente
    if (teamCharts.workload) {
        teamCharts.workload.destroy();
    }
    
    const memberNames = members.map(m => m.name);
    const utilization = members.map(m => m.utilization);
    const currentTasks = members.map(m => m.current_tasks);
    
    teamCharts.workload = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: memberNames,
            datasets: [
                {
                    label: 'Utilización (%)',
                    data: utilization,
                    backgroundColor: utilization.map(u => 
                        u > 80 ? '#EF4444' : u > 60 ? '#F59E0B' : '#10B981'
                    ),
                    yAxisID: 'y',
                    order: 1
                },
                {
                    label: 'Tareas Activas',
                    data: currentTasks,
                    backgroundColor: '#3B82F6',
                    type: 'line',
                    yAxisID: 'y1',
                    order: 2,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Utilización (%)'
                    },
                    max: 100
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Tareas Activas'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.datasetIndex === 0) {
                                label += context.parsed.y.toFixed(1) + '%';
                            } else {
                                label += context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

function createSkillsChart(skillCoverage) {
    const ctx = document.getElementById('skillsChart').getContext('2d');
    
    if (teamCharts.skills) {
        teamCharts.skills.destroy();
    }
    
    // Ordenar habilidades por cobertura
    const sortedSkills = Object.entries(skillCoverage)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // Top 10 habilidades
    
    teamCharts.skills = new Chart(ctx, {
        type: 'horizontalBar',
        data: {
            labels: sortedSkills.map(([skill]) => skill),
            datasets: [{
                label: 'Miembros con esta habilidad',
                data: sortedSkills.map(([, count]) => count),
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                    '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                    '#7FFFD4', '#FF69B4'
                ],
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function createSkillsDistribution(members) {
    const container = document.getElementById('skillsDistribution');
    
    // Agrupar habilidades por nivel
    const skillsByLevel = {
        'junior': new Set(),
        'mid': new Set(),
        'senior': new Set(),
        'expert': new Set()
    };
    
    members.forEach(member => {
        member.skills.forEach(skill => {
            skillsByLevel[member.skill_level].add(skill);
        });
    });
    
    container.innerHTML = Object.entries(skillsByLevel).map(([level, skills]) => {
        const skillCount = skills.size;
        const levelNames = {
            'junior': 'Junior',
            'mid': 'Mid-Level', 
            'senior': 'Senior',
            'expert': 'Expert'
        };
        
        const colors = {
            'junior': 'bg-blue-100 text-blue-800',
            'mid': 'bg-green-100 text-green-800',
            'senior': 'bg-purple-100 text-purple-800',
            'expert': 'bg-orange-100 text-orange-800'
        };
        
        return `
            <div class="text-center p-4 border border-gray-200 rounded-lg">
                <div class="text-2xl font-bold ${colors[level].split(' ')[1]}">${skillCount}</div>
                <div class="text-sm font-medium ${colors[level].split(' ')[0]} p-2 rounded-lg mt-2">
                    ${levelNames[level]}
                </div>
                <div class="text-xs text-gray-600 mt-2">habilidades únicas</div>
                <div class="mt-3 text-xs text-gray-500 max-h-20 overflow-y-auto">
                    ${Array.from(skills).slice(0, 5).join(', ')}${skillCount > 5 ? '...' : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Auto-refresh cada 2 minutos
setInterval(loadTeamMetrics, 120000);