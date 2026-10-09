function showToast(msg) {
            const toast = document.getElementById('toastNotice');
            toast.textContent = msg;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 2600);
        }

        function switchTab(tabId, btnElement) {
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            const targetPane = document.getElementById(tabId);
            if (targetPane) targetPane.classList.add('active');

            if (btnElement) {
                btnElement.classList.add('active');
            } else {
                const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
                if (btn) btn.classList.add('active');
            }
        }

        let isThresholdEditing = false;

        function updateRulePreviews() {
            const safe = parseInt(document.getElementById('inputSafeThreshold').value) || 3;
            const crit = parseInt(document.getElementById('inputCriticalThreshold').value) || 7;
            
            document.getElementById('previewSafe').textContent = `🟢 Safe: ≤ ${safe} people`;
            document.getElementById('previewWarning').textContent = `🟡 Warning: ${safe + 1} to ${crit} people`;
            document.getElementById('previewCritical').textContent = `🔴 Critical Surge: > ${crit} people`;
            document.getElementById('kpiRulesSummary').textContent = `Safe ≤${safe} | Surge >${crit}`;
        }

        const safeInputElem = document.getElementById('inputSafeThreshold');
        const critInputElem = document.getElementById('inputCriticalThreshold');
        if (safeInputElem) {
            safeInputElem.addEventListener('focus', () => { isThresholdEditing = true; });
            safeInputElem.addEventListener('input', () => { isThresholdEditing = true; updateRulePreviews(); });
        }
        if (critInputElem) {
            critInputElem.addEventListener('focus', () => { isThresholdEditing = true; });
            critInputElem.addEventListener('input', () => { isThresholdEditing = true; updateRulePreviews(); });
        }

        // Fetch Data & Populate Camera Table
        async function fetchAdminData() {
            try {
                const res = await fetch('/api/admin/info');
                if (!res.ok) return;
                const data = await res.json();

                // Cameras Table
                const tbody = document.getElementById('cameraTableBody');
                tbody.innerHTML = '';
                const cams = data.cameras || {};
                const camKeys = Object.keys(cams);
                document.getElementById('kpiCamCount').textContent = `${camKeys.length} Streams`;

                if (camKeys.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #8da2c0; padding: 24px;">No camera streams configured yet.</td></tr>`;
                } else {
                    camKeys.forEach(cid => {
                        const c = cams[cid];
                        const isConn = c.connected;
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><code>${cid}</code></td>
                            <td><strong>${c.name}</strong></td>
                            <td><code>${c.ip}</code></td>
                            <td style="color: #94a3b8; font-family: monospace; font-size: 11px; word-break: break-all;">${c.url}</td>
                            <td>
                                <span class="badge-status ${isConn ? 'badge-online' : 'badge-disabled'}">
                                    ${isConn ? '● LIVE' : '● OFFLINE'}
                                </span>
                            </td>
                            <td style="text-align: right;">
                                <button class="btn-table-action btn-delete" onclick="handleDeleteCamera('${cid}')">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"/>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                    </svg>
                                    Delete
                                </button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                }

                if (!isThresholdEditing) {
                    if (data.safe_threshold !== undefined) {
                        document.getElementById('inputSafeThreshold').value = data.safe_threshold;
                    }
                    if (data.critical_threshold !== undefined) {
                        document.getElementById('inputCriticalThreshold').value = data.critical_threshold;
                    }
                    updateRulePreviews();
                } else {
                    const safe = parseInt(document.getElementById('inputSafeThreshold').value) || data.safe_threshold || 3;
                    const crit = parseInt(document.getElementById('inputCriticalThreshold').value) || data.critical_threshold || 7;
                    document.getElementById('kpiRulesSummary').textContent = `Safe ≤${safe} | Surge >${crit}`;
                }

            } catch (e) {
                console.error("Admin fetch error:", e);
            }
        }

        async function handleAddCamera(e) {
            e.preventDefault();
            const id = document.getElementById('newCamId').value.trim();
            const name = document.getElementById('newCamName').value.trim();
            const ip = document.getElementById('newCamIp').value.trim();
            const url = document.getElementById('newCamUrl').value.trim();

            const res = await fetch('/api/admin/cameras/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, name, ip, url })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Camera ${name} added successfully!`);
                document.getElementById('addCamForm').reset();
                fetchAdminData();
            } else {
                alert('Error adding camera: ' + (data.error || 'Unknown error'));
            }
        }

        async function handleDeleteCamera(camId) {
            if (!confirm(`Are you sure you want to delete ${camId}?`)) return;
            const res = await fetch('/api/admin/cameras/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: camId })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Camera ${camId} removed.`);
                fetchAdminData();
            } else {
                alert('Error deleting camera: ' + (data.error || 'Failed'));
            }
        }

        async function handleUpdateThresholds(e) {
            e.preventDefault();
            const safeInput = document.getElementById('inputSafeThreshold');
            const critInput = document.getElementById('inputCriticalThreshold');
            const safe = parseInt(safeInput.value);
            const crit = parseInt(critInput.value);
            
            if (isNaN(safe) || isNaN(crit)) {
                alert("Please enter valid numbers for thresholds.");
                return;
            }

            if (safe < 1) {
                alert("Safe threshold must be at least 1 person.");
                return;
            }

            if (safe >= crit) {
                alert("Safe threshold must be less than critical threshold.");
                return;
            }

            try {
                const res = await fetch('/api/admin/thresholds/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ safe, critical: crit })
                });
                const data = await res.json();
                if (data.success) {
                    isThresholdEditing = false;
                    safeInput.value = data.safe;
                    critInput.value = data.critical;
                    safeInput.blur();
                    critInput.blur();
                    updateRulePreviews();
                    showToast(`Threshold rules saved: Safe ≤ ${data.safe}, Surge > ${data.critical}`);
                } else {
                    alert('Error updating thresholds: ' + (data.error || 'Unknown error'));
                }
            } catch (err) {
                console.error("Error updating thresholds:", err);
                alert("Network error updating thresholds.");
            }
        }

        function exportIncidentLog() {
            const incidents = [
                { id: "INC-2026-001", time: "2026-10-07 10:17:19", camera: "Camera 2", peak: 9, severity: "CRITICAL", action: "Dispersal Warning" },
                { id: "INC-2026-002", time: "2026-10-07 09:45:10", camera: "Camera 1", peak: 5, severity: "WARNING", action: "Patrol Officer Notified" }
            ];
            const blob = new Blob([JSON.stringify(incidents, null, 2)], { type: 'application/json' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `incident_report_${Date.now()}.json`;
            a.click();
            showToast('Incident audit report downloaded.');
        }

        // Initial Load & polling
        fetchAdminData();
        setInterval(fetchAdminData, 4000);
