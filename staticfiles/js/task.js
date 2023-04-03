$(document).ready(function() {
    $('#tasks-table').DataTable({
        "paging": true, // add pagination
        "searching": true, // enable search
        "ordering": true, // enable sorting
        "order": [[ 0, "desc" ]], // set default sort order to the first column
        "columnDefs": [ // add filter input to the "Loja" column
            {
                "targets": 2, // index of the "Loja" column (0-based)
                "type": "html", // use HTML input type
                "render": function(data, type, full, meta) {
                    return '<input type="text" class="form-control form-control-sm" placeholder="Filter" />';
                }
            }
        ]
    });

    // filter the table when the user types in the input field
    $('#tasks-table').on('keyup', 'thead input', function() {
        var index = $(this).parent().index(); // get the column index
        var value = $(this).val().toLowerCase(); // get the input value
        $('#tasks-table').DataTable().column(index).search(value).draw(); // filter the table
    });
});
