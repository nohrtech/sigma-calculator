$(document).ready(function() {
    // Hide loading spinner initially
    $('.loading').hide();
    
    // Handle file upload form submission
    $('#uploadForm').on('submit', function(e) {
        e.preventDefault();
        
        const fileInput = $('#file')[0];
        const files = fileInput.files;
        
        if (files.length === 0) {
            alert('Please select a file to upload');
            return;
        }
        
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('file', files[i]);
        }
        
        // Show loading spinner
        $('.loading').show();
        
        // Send file to server
        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // Hide loading spinner
                $('.loading').hide();
                
                if ($('#openInNewTab').is(':checked')) {
                    // Open results in new tab
                    const newTab = window.open('', '_blank');
                    newTab.document.write(response);
                } else {
                    // Replace current page with results
                    document.open();
                    document.write(response);
                    document.close();
                }
            },
            error: function(xhr, status, error) {
                $('.loading').hide();
                alert('Error processing file: ' + error);
            }
        });
    });
    
    // Handle comparison form submission
    $('#compareForm').on('submit', function(e) {
        e.preventDefault();
        
        const file1 = $('#file1')[0].files[0];
        const file2 = $('#file2')[0].files[0];
        
        if (!file1 || !file2) {
            alert('Please select two files to compare');
            return;
        }
        
        const formData = new FormData();
        formData.append('file1', file1);
        formData.append('file2', file2);
        
        // Show loading spinner
        $('.loading').show();
        
        // Send files to server for comparison
        $.ajax({
            url: '/compare',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // Hide loading spinner
                $('.loading').hide();
                
                if (response.error) {
                    alert('Error: ' + response.error);
                    return;
                }
                
                // Display comparison results
                displayComparisonResults(response);
            },
            error: function(xhr, status, error) {
                $('.loading').hide();
                alert('Error comparing files: ' + error);
            }
        });
    });
    
    function displayComparisonResults(data) {
        const comparison = data.comparison;
        const tbody = $('#comparisonTable');
        tbody.empty();
        
        // Add file names
        $('#comparisonResults').show();
        
        // Add rows for each component
        ['horizontal', 'vertical', 'E', 'N', 'U'].forEach(comp => {
            const diff = comparison.differences[comp];
            const row = $('<tr>');
            
            row.append($('<td>').text(comp.charAt(0).toUpperCase() + comp.slice(1)));
            row.append($('<td>').text(diff.mean_diff.toFixed(3)));
            row.append($('<td>').text(diff.rms_diff.toFixed(3)));
            row.append($('<td>').text(diff.max_diff.toFixed(3)));
            row.append($('<td>').text(diff.std_diff.toFixed(3)));
            row.append($('<td>').text(diff.mean_diff_pct.toFixed(2) + '%'));
            row.append($('<td>').text(diff.rms_diff_pct.toFixed(2) + '%'));
            
            tbody.append(row);
        });
    }
});
