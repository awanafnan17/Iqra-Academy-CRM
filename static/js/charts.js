document.addEventListener("DOMContentLoaded", () => {
    // Utility to get CSS variable values
    const getStyleVar = (name) => {
        return getComputedStyle(document.documentElement).getPropertyValue(name).strip || 
               getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    };

    // Color definitions falling back to brand system
    const colors = {
        primary: getStyleVar("--primary-color") || "#5B5FEF",
        secondary: getStyleVar("--secondary-color") || "#7C3AED",
        green: getStyleVar("--accent-green") || "#16A34A",
        blue: getStyleVar("--accent-blue") || "#0EA5E9",
        orange: getStyleVar("--accent-orange") || "#F59E0B",
        red: getStyleVar("--accent-red") || "#EF4444",
        border: getStyleVar("--border-color") || "#e2e8f0"
    };

    // Global chart configurations
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.color = "#4b5563";
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
    
    // Global tooltip formatting to append PKR
    Chart.defaults.plugins.tooltip.callbacks.label = (context) => {
        let label = context.dataset.label || '';
        if (label) {
            label += ': ';
        }
        const val = context.raw;
        if (val !== undefined && val !== null) {
            label += new Intl.NumberFormat().format(val) + ' PKR';
        }
        return label;
    };

    let isUnloading = false;
    const controller = new AbortController();
    const signal = controller.signal;

    window.addEventListener('beforeunload', () => {
        isUnloading = true;
        controller.abort();
    });

    // Helper to fetch data safely
    const fetchApi = async (url) => {
        try {
            const response = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                signal: signal
            });
            if (!response.ok) return null;
            const res = await response.json();
            return res.status === "success" ? res.data : null;
        } catch (e) {
            if (!isUnloading && e.name !== 'AbortError') {
                console.error("Failed fetching analytics endpoint:", e);
            }
            return null;
        }
    };

    // 1. Line Chart: Revenue Trend
    const revenueEl = document.getElementById("revenueChart");
    if (revenueEl) {
        fetchApi("/api/analytics/revenue-trend/").then((data) => {
            if (!data) return;
            const ctx = revenueEl.getContext("2d");
            
            const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const tuition = data.map(d => d.tuition);
            const lateFees = data.map(d => d.late_fees);
            const net = data.map(d => d.net);

            new Chart(ctx, {
                type: "line",
                data: {
                    labels: months,
                    datasets: [
                        {
                            label: "Tuition Revenue",
                            data: tuition,
                            borderColor: colors.primary,
                            backgroundColor: "rgba(91, 95, 239, 0.1)",
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: "Late Fees",
                            data: lateFees,
                            borderColor: colors.orange,
                            backgroundColor: "transparent",
                            borderWidth: 2,
                            borderDash: [5, 5],
                            tension: 0.4
                        },
                        {
                            label: "Net Cash Flow",
                            data: net,
                            borderColor: colors.green,
                            backgroundColor: "rgba(22, 163, 74, 0.05)",
                            borderWidth: 2.5,
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    plugins: {
                        legend: { position: "top", labels: { boxWidth: 12, usePointStyle: true } }
                    },
                    scales: {
                        y: { 
                            grid: { color: "#e2e8f0" }, 
                            ticks: { callback: value => "PKR " + new Intl.NumberFormat().format(value) },
                            title: { display: true, text: 'Revenue (PKR)' }
                        },
                        x: { grid: { display: false } }
                    }
                }
            });
        });
    }

    // 2. Bar Chart: Attendance Trend
    const attendanceEl = document.getElementById("attendanceChart");
    if (attendanceEl) {
        fetchApi("/api/analytics/attendance-trend/").then((data) => {
            if (!data || data.length === 0) {
                // Display placeholder text if no records
                attendanceEl.parentElement.innerHTML = "<div class='text-center text-muted py-5'>No attendance records available.</div>";
                return;
            }
            const ctx = attendanceEl.getContext("2d");
            
            // Limit to last 10 dates for clean sizing
            const limited = data.slice(-10);
            const labels = limited.map(d => d.date);
            const present = limited.map(d => d.present);
            const absent = limited.map(d => d.absent);
            const late = limited.map(d => d.late);

            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [
                        { label: "Present", data: present, backgroundColor: colors.green },
                        { label: "Late", data: late, backgroundColor: colors.orange },
                        { label: "Absent", data: absent, backgroundColor: colors.red }
                    ]
                },
                options: {
                    plugins: {
                        legend: { position: "top", labels: { boxWidth: 12 } }
                    },
                    scales: {
                        y: { stacked: true, grid: { color: "#e2e8f0" } },
                        x: { stacked: true, grid: { display: false } }
                    }
                }
            });
        });
    }

    // 3. Line/Bar Chart: Enrollment Growth
    const growthEl = document.getElementById("growthChart");
    if (growthEl) {
        fetchApi("/api/analytics/enrollment-growth/").then((data) => {
            if (!data) return;
            const ctx = growthEl.getContext("2d");
            
            const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const newEnrollments = data.map(d => d.new_enrollments);
            const cumulative = data.map(d => d.cumulative_enrollments);

            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: months,
                    datasets: [
                        {
                            type: "bar",
                            label: "New Enrollments",
                            data: newEnrollments,
                            backgroundColor: colors.blue,
                            borderRadius: 6
                        },
                        {
                            type: "line",
                            label: "Cumulative Total",
                            data: cumulative,
                            borderColor: colors.secondary,
                            borderWidth: 3,
                            fill: false,
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    plugins: {
                        legend: { position: "top" }
                    },
                    scales: {
                        y: { grid: { color: "#e2e8f0" } },
                        x: { grid: { display: false } }
                    }
                }
            });
        });
    }

    // 4. Donut Chart: Conversion Funnel
    const conversionEl = document.getElementById("conversionChart");
    if (conversionEl) {
        fetchApi("/api/analytics/lead-funnel/").then((data) => {
            if (!data) return;
            const ctx = conversionEl.getContext("2d");
            
            const funnel = data.funnel;
            const labels = funnel.map(f => f.status);
            const counts = funnel.map(f => f.count);

            new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: labels,
                    datasets: [{
                        data: counts,
                        backgroundColor: [colors.blue, colors.secondary, colors.orange, colors.green, colors.red],
                        borderWidth: 2,
                        borderColor: "#ffffff"
                    }]
                },
                options: {
                    plugins: {
                        legend: { position: "right", labels: { boxWidth: 12, usePointStyle: true } }
                    },
                    cutout: "70%"
                }
            });
        });
    }

    // 5. Horizontal Bar Chart: Overdue Aging Report
    const agingEl = document.getElementById("agingChart");
    if (agingEl) {
        fetchApi("/api/analytics/aging-report/").then((data) => {
            if (!data) return;
            const ctx = agingEl.getContext("2d");
            
            const labels = ["Current", "1-30 Days", "31-60 Days", "61-90 Days", "90+ Days"];
            const amounts = [data.current, data['1_30'], data['31_60'], data['61_90'], data['90_plus']];

            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Outstanding Balances (PKR)",
                        data: amounts,
                        backgroundColor: [colors.blue, colors.orange, colors.orange, colors.red, colors.red],
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y', // Makes it a horizontal bar chart
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: { 
                            grid: { color: "#e2e8f0" },
                            ticks: { callback: value => "PKR " + new Intl.NumberFormat().format(value) }
                        },
                        y: { grid: { display: false } }
                    }
                }
            });
        });
    }
});
