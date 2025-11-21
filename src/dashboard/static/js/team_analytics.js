// src/dashboard/static/js/team_analytics.js
let teamCharts = {};

async function loadTeamMetrics() {
    const period = document.getElementById('periodSelect').value;
    try {
        const [teamMetrics, memberMetrics] = await Promise.all([
            fetch(`/dashboard/api/team-metrics?days=${period}`).then(r => r.json()),
            fetch(`/dashboard/api/member-metrics?days=${period}`).then(r => r.json())
        ]);

        if (teamMetrics && Object.keys(teamMetrics).length > 0) {
            updateMainMetrics(teamMetrics);
            createSkillsChart(teamMetrics.skill_coverage || {});
        }
        
        if (memberMetrics && memberMetrics.members) {
            updateMembersTable(memberMetrics.members);
            createWorkloadChart(memberMetrics.members);
            createSkillsDistribution(memberMetrics.members);
        }
    } catch (error) { console.error('Error:', error); }
}

function updateMainMetrics(m) {
    document.getElementById('totalMembers').textContent = m.total_members || 0;
    document.getElementById('availableMembers').textContent = `${m.available_members || 0} disponibles`;
    document.getElementById('totalTasks').textContent = m.total_tasks_assigned || 0;
    document.getElementById('completedTasks').textContent = `${m.total_tasks_completed || 0} completadas`;
    const rate = m.completion_rate ? m.completion_rate.toFixed(1) : "0.0";
    document.getElementById('completionRate').textContent = `${rate}%`;
    document.getElementById('busyMembers').textContent = m.busy_members ? m.busy_members.length : 0;
}

function updateMembersTable(members) {
    const table = document.getElementById('teamMembersTable');
    if (!table) return;
    if (!members.length) { table.innerHTML = '<tr><td colspan="7" class="text-center p-4">Sin datos</td></tr>'; return; }

    table.innerHTML = members.map(m => {
        const utiliz = m.utilization !== undefined ? m.utilization : 0;
        const color = utiliz > 80 ? 'red' : utiliz > 60 ? 'yellow' : 'green';
        return `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4"><div class="font-medium">${m.name}</div></td>
            <td class="px-6 py-4 text-sm">${m.current_tasks} tareas</td>
            <td class="px-6 py-4 text-sm">${m.completed_tasks} comp.</td>
            <td class="px-6 py-4"><div class="w-full bg-gray-200 rounded-full h-2"><div class="bg-${color}-600 h-2 rounded-full" style="width:${Math.min(utiliz,100)}%"></div></div></td>
            <td class="px-6 py-4 text-sm">${m.success_rate ? m.success_rate.toFixed(1) : '0.0'}%</td>
            <td class="px-6 py-4 text-sm">${m.avg_completion_time ? m.avg_completion_time.toFixed(1) : '-'}h</td>
            <td class="px-6 py-4"><span class="px-2 rounded-full text-xs ${m.available ? 'bg-green-100 text-green-800':'bg-red-100 text-red-800'}">${m.available?'Disp':'Ocup'}</span></td>
        </tr>`;
    }).join('');
}

function createWorkloadChart(members) {
    const ctx = document.getElementById('workloadChart').getContext('2d');
    if (teamCharts.workload) teamCharts.workload.destroy();
    
    teamCharts.workload = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: members.map(m => m.name.split(' ')[0]),
            datasets: [{
                label: 'Utilización (%)',
                data: members.map(m => m.utilization || 0),
                backgroundColor: members.map(m => (m.utilization||0)>80?'#EF4444':'#3B82F6')
            }]
        },
        options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } }
    });
}

function createSkillsChart(skills) {
    const ctx = document.getElementById('skillsChart').getContext('2d');
    if (teamCharts.skills) teamCharts.skills.destroy();
    const sorted = Object.entries(skills).sort((a,b)=>b[1]-a[1]).slice(0,8);
    
    teamCharts.skills = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(s=>s[0]),
            datasets: [{ label: 'Expertos', data: sorted.map(s=>s[1]), backgroundColor: '#8B5CF6' }]
        },
        options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } } }
    });
}

function createSkillsDistribution(members) {
    const div = document.getElementById('skillsDistribution');
    if(!div) return;
    const lvls = {};
    members.forEach(m => {
        let l = m.skill_level || 'Unknown';
        if(typeof l === 'object') l = l.value;
        l = String(l).toUpperCase();
        lvls[l] = (lvls[l]||0)+1;
    });
    div.innerHTML = Object.entries(lvls).map(([k,v]) => `
        <div class="p-4 bg-gray-50 rounded text-center border"><div class="text-2xl font-bold">${v}</div><div class="text-xs text-gray-500">${k}</div></div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', loadTeamMetrics);
setInterval(loadTeamMetrics, 300000);