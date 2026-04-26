// Global state
let currentPlan = null;
let currentPlanId = null;
let allPlans = [];

// API Configuration
const API_BASE = '/api';
const STREAMING = true;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkHealth();
    loadPlanHistory();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('hypothesisForm').addEventListener('submit', handleGeneratePlan);
    document.getElementById('resetBtn').addEventListener('click', resetForm);
    document.getElementById('downloadBtn').addEventListener('click', downloadPlan);
    document.getElementById('sharePlanBtn').addEventListener('click', savePlan);
    document.getElementById('feedbackForm').addEventListener('submit', handleFeedback);
}

// Check API health
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        const healthStatus = document.getElementById('health-status');
        healthStatus.textContent = '● Online';
        healthStatus.style.color = '#16a34a';
    } catch (err) {
        const healthStatus = document.getElementById('health-status');
        healthStatus.textContent = '● Offline';
        healthStatus.style.color = '#dc2626';
    }
}

// Handle plan generation
async function handleGeneratePlan(e) {
    e.preventDefault();
    
    const hypothesis = document.getElementById('hypothesis').value;
    const domain = document.getElementById('domain').value;
    
    if (!hypothesis.trim()) {
        showToast('Please enter a hypothesis', 'error');
        return;
    }
    
    // Show progress, hide results
    document.getElementById('resultsSection').classList.add('d-none');
    document.getElementById('progressSection').classList.remove('d-none');
    document.getElementById('submitSpinner').classList.remove('d-none');
    document.getElementById('submitText').textContent = 'Generating...';
    
    try {
        if (STREAMING) {
            await generateWithStreaming(hypothesis, domain);
        } else {
            await generateWithoutStreaming(hypothesis, domain);
        }
    } catch (err) {
        console.error('Generation error:', err);
        showToast(`Error: ${err.message}`, 'error');
    } finally {
        document.getElementById('submitSpinner').classList.add('d-none');
        document.getElementById('submitText').textContent = 'Generate Plan';
    }
}

// Generate with streaming (real-time progress)
async function generateWithStreaming(hypothesis, domain) {
    const eventLog = document.getElementById('eventLog');
    const progressBar = document.getElementById('progressBar');
    
    eventLog.innerHTML = '';
    let eventCount = 0;
    const totalEvents = 8;
    
    try {
        const response = await fetch(`${API_BASE}/run/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hypothesis, domain })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const event = JSON.parse(line.slice(6));
                        
                        if (event.type === 'node_start') {
                            addEventLog(`Starting: ${event.node}`, eventLog, false);
                        } else if (event.type === 'node_complete') {
                            addEventLog(`✓ Completed: ${event.node}`, eventLog, true);
                            eventCount++;
                            progressBar.style.width = `${(eventCount / totalEvents) * 100}%`;
                        } else if (event.type === 'error') {
                            addEventLog(`✗ Error: ${event.message}`, eventLog, false, true);
                        } else if (event.type === 'complete') {
                            currentPlan = event.plan;
                            currentPlanId = event.plan_id;
                            
                            document.getElementById('progressSection').classList.add('d-none');
                            displayPlan(event.plan);
                            document.getElementById('resultsSection').classList.remove('d-none');
                            
                            loadPlanHistory();
                            showToast('Plan generated successfully!', 'success');
                        }
                    } catch (e) {
                        console.error('Event parse error:', e);
                    }
                }
            }
        }
    } catch (err) {
        throw new Error(`Streaming failed: ${err.message}`);
    }
}

// Generate without streaming (simpler)
async function generateWithoutStreaming(hypothesis, domain) {
    const response = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hypothesis, domain })
    });
    
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    
    const data = await response.json();
    currentPlan = data.plan;
    currentPlanId = data.plan_id;
    
    document.getElementById('progressSection').classList.add('d-none');
    displayPlan(data.plan);
    document.getElementById('resultsSection').classList.remove('d-none');
    
    loadPlanHistory();
    showToast('Plan generated successfully!', 'success');
}

// Display plan results
function displayPlan(plan) {
    // Quality score
    const score = plan.quality_score || 0;
    document.getElementById('qualityScore').textContent = Math.round(score);
    
    const badge = document.getElementById('qualityBadge');
    let badgeText = 'Fair';
    let badgeClass = 'quality-fair';
    
    if (score >= 80) {
        badgeText = 'Excellent';
        badgeClass = 'quality-excellent';
    } else if (score >= 60) {
        badgeText = 'Good';
        badgeClass = 'quality-good';
    } else if (score >= 40) {
        badgeText = 'Fair';
        badgeClass = 'quality-fair';
    } else {
        badgeText = 'Poor';
        badgeClass = 'quality-poor';
    }
    
    badge.className = `quality-badge ${badgeClass}`;
    badge.textContent = badgeText;
    
    // Quality errors
    if (plan.quality_errors && plan.quality_errors.length > 0) {
        const errorHtml = plan.quality_errors
            .map(e => `<div class="mb-2"><strong>⚠️</strong> ${e}</div>`)
            .join('');
        document.getElementById('qualityErrors').innerHTML = errorHtml;
    }
    
    // Refined hypothesis
    const refined = plan.refined_hypothesis || {};
    document.getElementById('refinedContent').innerHTML = `
        <div class="section-title">Refined Statement</div>
        <p><strong>If:</strong> ${refined.if_statement || 'N/A'}</p>
        <p><strong>Then:</strong> ${refined.then_statement || 'N/A'}</p>
        <p><strong>Because:</strong> ${refined.because_statement || 'N/A'}</p>
        
        ${refined.sub_hypotheses ? `
            <div class="section-title mt-4">Sub-Hypotheses</div>
            ${refined.sub_hypotheses.map((h, i) => `<div class="mb-2">H${i+1}: ${h}</div>`).join('')}
        ` : ''}
        
        ${refined.alternative_hypotheses ? `
            <div class="section-title mt-4">Alternative Hypotheses</div>
            ${refined.alternative_hypotheses.map((h, i) => `<div class="mb-2">Alt${i+1}: ${h}</div>`).join('')}
        ` : ''}
        
        ${refined.expected_outcomes ? `
            <div class="section-title mt-4">Expected Outcomes</div>
            ${refined.expected_outcomes.map((o, i) => `<div class="mb-2">• ${o}</div>`).join('')}
        ` : ''}
    `;
    
    // Literature
    const literature = plan.literature_review || {};
    document.getElementById('literatureContent').innerHTML = `
        <div class="section-title">Gap Analysis</div>
        <p>${literature.gap_analysis || 'No gap analysis available'}</p>
        
        ${literature.papers ? `
            <div class="section-title">Key Papers</div>
            ${literature.papers.map((p, i) => `
                <div class="mb-3">
                    <h6>${i+1}. ${p.title}</h6>
                    <p class="mb-1"><small><strong>Authors:</strong> ${(p.authors || []).join(', ')}</small></p>
                    <p class="mb-1"><small><strong>Year:</strong> ${p.year}</small></p>
                    <p class="mb-1"><small>${p.abstract_summary || p.abstract || 'No abstract available'}</small></p>
                </div>
            `).join('')}
        ` : ''}
    `;
    
    // Protocol
    const protocol = plan.protocol || {};
    document.getElementById('protocolContent').innerHTML = `
        <div class="section-title">Experimental Steps</div>
        ${(protocol.steps || []).map((step, i) => `
            <div class="protocol-step">
                <strong>Step ${i+1}:</strong> ${step.description || step}
                ${step.equipment_needed ? `<div class="mt-2"><small>Equipment: ${Array.isArray(step.equipment_needed) ? step.equipment_needed.join(', ') : step.equipment_needed}</small></div>` : ''}
                ${step.duration_minutes ? `<div class="mt-1"><small>Duration: ${step.duration_minutes} min</small></div>` : ''}
            </div>
        `).join('')}
    `;
    
    // Materials
    const materials = plan.materials || {};
    document.getElementById('materialsContent').innerHTML = `
        <div class="section-title">Required Materials</div>
        ${(materials.reagents || []).map((m, i) => `
            <div class="materials-item">
                <strong>${m.name || m}</strong>
                ${m.catalog_number ? `<br><small>Catalog: ${m.catalog_number}</small>` : ''}
                ${m.quantity ? `<br><small>Qty: ${m.quantity}</small>` : ''}
                ${m.supplier ? `<br><small>Supplier: ${m.supplier}</small>` : ''}
                ${m.cost ? `<br><small>Cost: $${m.cost}</small>` : ''}
            </div>
        `).join('')}
    `;
    
    // Budget
    const budget = plan.budget || {};
    document.getElementById('budgetContent').innerHTML = `
        <div class="section-title">Cost Breakdown</div>
        <table class="table table-sm">
            <thead>
                <tr><th>Item</th><th class="text-end">Cost</th></tr>
            </thead>
            <tbody>
                ${(budget.line_items || []).map(item => `
                    <tr>
                        <td>${item.description || item.category || item}</td>
                        <td class="text-end">$${typeof item === 'object' ? (item.amount || item.cost || 0) : 0}</td>
                    </tr>
                `).join('')}
                <tr class="table-active"><td><strong>Total</strong></td><td class="text-end"><strong>$${budget.total || 0}</strong></td></tr>
            </tbody>
        </table>
    `;
    
    // Timeline
    const timeline = plan.timeline || {};
    document.getElementById('timelineContent').innerHTML = `
        <div class="section-title">Project Timeline</div>
        ${(timeline.phases || []).map((phase, i) => `
            <div class="timeline-item">
                <div class="timeline-marker">${i+1}</div>
                <div class="flex-grow-1">
                    <h6>${phase.name || phase}</h6>
                    <p class="mb-1"><small>Duration: ${phase.duration_days || 'TBD'} days</small></p>
                    ${phase.milestone ? `<p class="mb-0"><small><strong>Milestone:</strong> ${phase.milestone}</small></p>` : ''}
                </div>
            </div>
        `).join('')}
    `;
    
    // Validation
    const validation = plan.validation || {};
    document.getElementById('validationContent').innerHTML = `
        <div class="section-title">Validation Approach</div>
        <p><strong>Method:</strong> ${validation.statistical_test || 'Not specified'}</p>
        <p><strong>Sample Size:</strong> ${validation.sample_size || 'Not specified'}</p>
        <p><strong>Power:</strong> ${validation.power_level || 'Not specified'}</p>
        <p><strong>Significance Level:</strong> α = ${validation.alpha || 0.05}</p>
        ${validation.controls ? `
            <div class="mt-3">
                <strong>Controls:</strong>
                ${Array.isArray(validation.controls) ? validation.controls.map(c => `<div>• ${c}</div>`).join('') : `<div>• ${validation.controls}</div>`}
            </div>
        ` : ''}
    `;
    
    // Safety
    const safety = plan.biosafety || {};
    document.getElementById('safetyContent').innerHTML = `
        <div class="section-title">Biosafety Assessment</div>
        <div class="alert alert-warning">
            <strong>BSL Level:</strong> ${safety.bsl_level || 'BSL-1'}
        </div>
        <p><strong>PPE Required:</strong> ${safety.ppe_requirements || 'Standard'}</p>
        <p><strong>Waste Disposal:</strong> ${safety.waste_disposal || 'Standard biological waste'}</p>
        ${safety.risks ? `
            <div class="mt-3">
                <strong>Identified Risks:</strong>
                ${Array.isArray(safety.risks) ? safety.risks.map((r, i) => `
                    <div class="mb-2">
                        <strong>Risk ${i+1}:</strong> ${typeof r === 'string' ? r : r.description}
                        ${typeof r === 'object' && r.mitigation ? `<div class="small mt-1">Mitigation: ${r.mitigation}</div>` : ''}
                    </div>
                `).join('') : ''}
            </div>
        ` : ''}
    `;
}

// Add event to log
function addEventLog(message, container, isComplete = false, isError = false) {
    const item = document.createElement('div');
    item.className = `event-item ${isComplete ? 'event-complete' : ''} ${isError ? 'event-error' : ''}`;
    item.textContent = message;
    container.appendChild(item);
    container.scrollTop = container.scrollHeight;
}

// Load plan history
async function loadPlanHistory() {
    try {
        const res = await fetch(`${API_BASE}/plans?limit=10&offset=0`);
        const data = await res.json();
        
        allPlans = data.plans || [];
        
        if (allPlans.length === 0) {
            document.getElementById('plansList').innerHTML = '';
            document.getElementById('noPlans').classList.remove('d-none');
            return;
        }
        
        document.getElementById('noPlans').classList.add('d-none');
        
        const plansList = allPlans.map(plan => `
            <div class="plan-item" onclick="loadPlanDetail('${plan.id}')">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${plan.refined_hypothesis?.if_statement?.substring(0, 60) || 'Untitled'}</h6>
                        <small class="text-muted">Score: ${Math.round(plan.quality_score || 0)}/100</small>
                    </div>
                    <span class="badge bg-primary">${new Date(plan.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
        
        document.getElementById('plansList').innerHTML = plansList;
        
        // Update feedback dropdown
        const feedbackSelect = document.getElementById('feedbackPlan');
        const currentValue = feedbackSelect.value;
        feedbackSelect.innerHTML = '<option value="">Choose a plan...</option>' + 
            allPlans.map(p => `<option value="${p.id}">${p.refined_hypothesis?.if_statement?.substring(0, 50) || 'Plan'}</option>`).join('');
        feedbackSelect.value = currentValue;
    } catch (err) {
        console.error('Failed to load plans:', err);
    }
}

// Load plan detail
async function loadPlanDetail(planId) {
    try {
        const res = await fetch(`${API_BASE}/plan/${planId}`);
        if (!res.ok) throw new Error('Plan not found');
        
        const data = await res.json();
        currentPlan = data;
        currentPlanId = planId;
        
        // Switch to generate tab and display
        document.getElementById('mainTabs').querySelector('[data-bs-target="#generate"]').click();
        document.getElementById('progressSection').classList.add('d-none');
        displayPlan(data);
        document.getElementById('resultsSection').classList.remove('d-none');
        
        showToast('Plan loaded!', 'success');
    } catch (err) {
        showToast(`Error loading plan: ${err.message}`, 'error');
    }
}

// Reset form
function resetForm() {
    document.getElementById('hypothesisForm').reset();
    document.getElementById('resultsSection').classList.add('d-none');
    document.getElementById('progressSection').classList.add('d-none');
    document.getElementById('hypothesis').focus();
}

// Download plan as text
function downloadPlan() {
    if (!currentPlan) {
        showToast('No plan to download', 'error');
        return;
    }
    
    let content = 'THE AI SCIENTIST - EXPERIMENT PLAN\n';
    content += '='.repeat(50) + '\n\n';
    
    content += 'REFINED HYPOTHESIS\n';
    content += '-'.repeat(50) + '\n';
    const refined = currentPlan.refined_hypothesis || {};
    content += `If: ${refined.if_statement || 'N/A'}\n`;
    content += `Then: ${refined.then_statement || 'N/A'}\n`;
    content += `Because: ${refined.because_statement || 'N/A'}\n\n`;
    
    content += 'PROTOCOL\n';
    content += '-'.repeat(50) + '\n';
    const protocol = currentPlan.protocol || {};
    (protocol.steps || []).forEach((step, i) => {
        content += `${i+1}. ${step.description || step}\n`;
    });
    content += '\n';
    
    content += 'BUDGET\n';
    content += '-'.repeat(50) + '\n';
    const budget = currentPlan.budget || {};
    content += `Total Cost: $${budget.total || 0}\n`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `experiment_plan_${currentPlanId || 'export'}.txt`;
    a.click();
    
    showToast('Plan downloaded!', 'success');
}

// Save plan
async function savePlan() {
    if (!currentPlanId) {
        showToast('Plan not saved yet', 'error');
        return;
    }
    
    const planUrl = `${window.location.origin}/?plan=${currentPlanId}`;
    
    try {
        await navigator.clipboard.writeText(planUrl);
        showToast('Plan link copied to clipboard!', 'success');
    } catch (err) {
        showToast(`Plan ID: ${currentPlanId}`, 'info');
    }
}

// Submit feedback
async function handleFeedback(e) {
    e.preventDefault();
    
    const planId = document.getElementById('feedbackPlan').value;
    if (!planId) {
        showToast('Please select a plan', 'error');
        return;
    }
    
    const feedback = {
        plan_id: planId,
        section: document.getElementById('feedbackSection').value,
        original_content: document.getElementById('feedbackOriginal').value,
        correction: document.getElementById('feedbackCorrection').value,
        experiment_domain: 'cell_biology' // Can be extracted from plan
    };
    
    try {
        const res = await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feedback)
        });
        
        if (!res.ok) throw new Error('Failed to submit feedback');
        
        document.getElementById('feedbackForm').reset();
        showToast('Thank you! Your feedback helps improve the AI.', 'success');
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const bgClass = {
        success: 'bg-success',
        error: 'bg-danger',
        info: 'bg-info'
    }[type] || 'bg-info';
    
    const toast = document.createElement('div');
    toast.className = `toast ${bgClass} text-white`;
    toast.style.cssText = 'margin-bottom: 0.5rem; min-width: 300px;';
    toast.innerHTML = `
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
