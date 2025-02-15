let currentResults = null;

$(document).ready(function() {
    // Hide loading spinner initially
    $('.loading').hide();
    
    // Handle file upload form submission
    $('#uploadForm').on('submit', function(e) {
        e.preventDefault();
        
        const fileInput = $('#file')[0];
        const files = fileInput.files;
        
        if (files.length === 0) {
            showError('Please select a file to upload');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', files[0]);
        
        // Show loading spinner
        $('.loading').show();
        $('#error').hide();
        
        // Send file to server
        $.ajax({
            url: '/calculate',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('.loading').hide();
                
                if ($('#openInNewTab').is(':checked') && response.result_id) {
                    window.open(`/view_results/${response.result_id}`, '_blank');
                } else {
                    $('#results').show();
                    displayResults(response);
                }
                
                fileInput.value = '';
            },
            error: function(xhr) {
                $('.loading').hide();
                showError(xhr.responseJSON?.error || 'Error processing file');
            }
        });
    });
    
    // Handle comparison form submission
    $('#compareForm').on('submit', function(e) {
        e.preventDefault();
        
        const file1 = $('#file1')[0].files[0];
        const file2 = $('#file2')[0].files[0];
        
        if (!file1 || !file2) {
            showError('Please select two files to compare');
            return;
        }
        
        const formData = new FormData();
        formData.append('file1', file1);
        formData.append('file2', file2);
        
        // Show loading spinner
        $('.loading').show();
        $('#error').hide();
        
        // Send files to server for comparison
        $.ajax({
            url: '/compare',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('.loading').hide();
                
                if (response.error) {
                    showError(response.error);
                    return;
                }
                
                if ($('#compareOpenInNewTab').is(':checked') && response.result_id) {
                    window.open(`/view_comparison/${response.result_id}`, '_blank');
                } else {
                    displayComparisonResults(response);
                }
            },
            error: function(xhr) {
                $('.loading').hide();
                showError(xhr.responseJSON?.error || 'Error comparing files');
            }
        });
    });
    
    // Handle PDF download
    $('#downloadPdf').on('click', function() {
        if (!currentResults) {
            showError('No results available to download');
            return;
        }
        
        $.ajax({
            url: '/generate_pdf',
            type: 'POST',
            data: JSON.stringify(currentResults),
            contentType: 'application/json',
            xhrFields: {
                responseType: 'blob'
            },
            success: function(blob) {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'sigma_results.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            },
            error: function(xhr) {
                showError(xhr.responseJSON?.error || 'Error generating PDF');
            }
        });
    });
});

function displayResults(data) {
    currentResults = data;
    $('#results').show();
    
    if (data.epoch_data) {
        $('#epochResults').show();
        const tbody = $('#epochTableBody');
        tbody.empty();
        
        const displayEpochs = data.epoch_data.slice(0, 100);
        displayEpochs.forEach(epoch => {
            tbody.append(`
                <tr>
                    <td>${epoch.timestamp}</td>
                    <td>${epoch.horizontal}</td>
                    <td>${epoch.vertical}</td>
                    <td>${epoch.east}</td>
                    <td>${epoch.north}</td>
                    <td>${epoch.up}</td>
                </tr>
            `);
        });
        
        if (data.epoch_data.length > 100) {
            tbody.parent().parent().append(`
                <p class="text-muted mt-2">
                    Showing first 100 epochs out of ${data.epoch_data.length} total epochs
                </p>
            `);
        }
    } else {
        $('#epochResults').hide();
    }
    
    const summary = data.summary;
    $('#horizontalMean').text(summary.horizontal.mean);
    $('#horizontalMin').text(summary.horizontal.min);
    $('#horizontalMax').text(summary.horizontal.max);
    $('#horizontalStd').text(summary.horizontal.std);
    
    $('#verticalMean').text(summary.vertical.mean);
    $('#verticalMin').text(summary.vertical.min);
    $('#verticalMax').text(summary.vertical.max);
    $('#verticalStd').text(summary.vertical.std);
    
    $('#EMean').text(summary.E.mean);
    $('#EMin').text(summary.E.min);
    $('#EMax').text(summary.E.max);
    $('#EStd').text(summary.E.std);
    
    $('#NMean').text(summary.N.mean);
    $('#NMin').text(summary.N.min);
    $('#NMax').text(summary.N.max);
    $('#NStd').text(summary.N.std);
    
    $('#UMean').text(summary.U.mean);
    $('#UMin').text(summary.U.min);
    $('#UMax').text(summary.U.max);
    $('#UStd').text(summary.U.std);
}

function displayComparisonResults(data) {
    const comparison = data.comparison;
    const file1Results = $('#file1Results');
    const file2Results = $('#file2Results');
    const comparisonTable = $('#comparisonTable');
    
    // Clear all tables
    file1Results.empty();
    file2Results.empty();
    comparisonTable.empty();
    
    // Show comparison results section
    $('#comparisonResults').show();
    
    // Set file names
    $('#file1Name').text(data.file1_name || 'File 1');
    $('#file2Name').text(data.file2_name || 'File 2');
    
    // Display individual file results
    ['horizontal', 'vertical', 'E', 'N', 'U'].forEach(comp => {
        // File 1 results
        const stats1 = comparison.file1[comp];
        const row1 = $('<tr>');
        row1.append($('<td>').text(comp.charAt(0).toUpperCase() + comp.slice(1)));
        row1.append($('<td>').text(stats1.mean.toFixed(3)));
        row1.append($('<td>').text(stats1.rms.toFixed(3)));
        row1.append($('<td>').text(stats1.max.toFixed(3)));
        row1.append($('<td>').text(stats1.std.toFixed(3)));
        file1Results.append(row1);
        
        // File 2 results
        const stats2 = comparison.file2[comp];
        const row2 = $('<tr>');
        row2.append($('<td>').text(comp.charAt(0).toUpperCase() + comp.slice(1)));
        row2.append($('<td>').text(stats2.mean.toFixed(3)));
        row2.append($('<td>').text(stats2.rms.toFixed(3)));
        row2.append($('<td>').text(stats2.max.toFixed(3)));
        row2.append($('<td>').text(stats2.std.toFixed(3)));
        file2Results.append(row2);
        
        // Comparison results
        const diff = comparison.differences[comp];
        const rowComp = $('<tr>');
        
        rowComp.append($('<td>').text(comp.charAt(0).toUpperCase() + comp.slice(1)));
        rowComp.append($('<td>').text(diff.mean_diff.toFixed(3)));
        rowComp.append($('<td>').text(diff.rms_diff.toFixed(3)));
        rowComp.append($('<td>').text(diff.max_diff.toFixed(3)));
        rowComp.append($('<td>').text(diff.std_diff.toFixed(3)));
        
        // Add percentage differences with color coding
        const meanDiffPct = $('<td>').text(diff.mean_diff_pct.toFixed(2) + '%');
        const rmsDiffPct = $('<td>').text(diff.rms_diff_pct.toFixed(2) + '%');
        
        // Color code percentage differences
        if (Math.abs(diff.mean_diff_pct) > 10) {
            meanDiffPct.addClass('text-danger');
        } else if (Math.abs(diff.mean_diff_pct) > 5) {
            meanDiffPct.addClass('text-warning');
        } else {
            meanDiffPct.addClass('text-success');
        }
        
        if (Math.abs(diff.rms_diff_pct) > 10) {
            rmsDiffPct.addClass('text-danger');
        } else if (Math.abs(diff.rms_diff_pct) > 5) {
            rmsDiffPct.addClass('text-warning');
        } else {
            rmsDiffPct.addClass('text-success');
        }
        
        rowComp.append(meanDiffPct);
        rowComp.append(rmsDiffPct);
        
        comparisonTable.append(rowComp);
    });
}

function showError(message) {
    const errorDiv = $('#error');
    errorDiv.text(message);
    errorDiv.show();
    $('#results').hide();
    $('#epochResults').hide();
    $('#comparisonResults').hide();
}
