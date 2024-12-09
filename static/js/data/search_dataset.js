var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

let selectBox = new vanillaSelectBox("#rightsHolder", {
    placeHolder: gettext("來源資料庫"),
    search: true, disableSelectAll: true,
    translations: { "all": gettext("全部"), "items": gettext(" 個選項"), "clearAll": gettext("重設") }
});

let selectBox1 = new vanillaSelectBox("#taxonGroup", {
    placeHolder: gettext("物種類群"), search: false, disableSelectAll: true,
});



$(function () {

    $(document).on("keydown", "form", function(event) { 
        
        if (event.key == "Enter"){
            submitSearch(is_preload=false)
            return event.key != "Enter";
        }
    });
    

    $('.resetSearch').on('click', function () {
        $('#searchForm').trigger("reset");
        selectBox.empty()
        selectBox1.empty()
    })


    $('#taxonGroup').on('change', function () {
        if ($('#btn-group-taxonGroup .vsb-menu ul li.active').length > 0) {
          $('#btn-group-taxonGroup button span.title').addClass('black').removeClass('color-707070')
        } else {
          $('#btn-group-taxonGroup button span.title').addClass('color-707070').removeClass('black')
        }
      })
    
    $('#rightsHolder').on('change', function () {
        if ($('#btn-group-rightsHolder .vsb-menu ul li.active').length > 0) {
          $('#btn-group-rightsHolder button span.title').addClass('black').removeClass('color-707070')
        } else {
          $('#btn-group-rightsHolder button span.title').addClass('color-707070').removeClass('black')
        }
      })
    
    

    $('.submitSearch').on('click', function(){
        submitSearch(is_preload=false)
    })

    // 起始狀態
    // submitSearch(page, limit, orderby, sort, is_preload=true)
    submitSearch(is_preload=true)


    $('select[name=shownumber]').on('change', function () {
        submitSearch(is_preload=false)
    })


    $('.orderby').on('click', function () {
        if ($(this).children('svg').hasClass('fa-sort')) {
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-down sort-icon-active');
            $(this).data('sort', 'desc');
        } else if ($(this).children('svg').hasClass('fa-sort-down')) { // 如果原本是down (desc)
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-up sort-icon-active')
            $(this).data('sort', 'asc');
        } else {  // 如果原本是up (asc)
            $('.orderby:not(this)').children('svg').removeClass('fa-sort-down fa-sort-up sort-icon-active sort-icon').addClass('fa-sort sort-icon');
            $(this).children('svg').removeClass('fa-sort sort-icon-active sort-icon').addClass('fa-sort-down sort-icon-active')
            $(this).data('sort', 'desc');
        }
        submitSearch(is_preload=false)
    })

    // 下載
    $('.downloadDatasetList').on('click', function () {
        
        if ($('input[name=is_authenticated]').val() == 'True') {

            let orderby = $('.sort-icon-active').parent().data('orderby');
            let sort = $('.sort-icon-active').parent().data('sort');


            $('#searchForm').append(
                $('<input>', {type: 'hidden', name: 'orderby', value: orderby}),
                $('<input>', {type: 'hidden', name: 'sort', value: sort}),
            ).submit();
        } else {
            alert(gettext('請先登入'))
        }
    })


});



function submitSearch(is_preload, page){

    $(".loading_area").removeClass('d-none');

    page = page ? page : 1 ;
    let limit = $('select[name=shownumber]').find(':selected').val();
    let orderby = $('.sort-icon-active').parent().data('orderby');
    let sort = $('.sort-icon-active').parent().data('sort');

    $.ajax({
        url: "/get_conditional_dataset",
        data: $('#searchForm').serialize() + '&page=' + page + '&limit=' + limit + '&orderby=' + orderby +  '&sort=' + sort,
        type: 'POST',
        dataType: 'json',
    })
    .done(function (response) {
        
        $('.result_table tr:not(.table_title)').remove()
        $('.page-inf').remove()

        if (response.count == 0) {
    
            $('.table_title').addClass('d-none')
            $('.result_inf_top').addClass('d-none')
            $('.result_inf_top_1').addClass('d-none')
            $('.no_data').removeClass('d-none')

        } else {

            $('.table_title').removeClass('d-none')
    
            $('.result_inf_top').removeClass('d-none')
            $('.result_inf_top_1').removeClass('d-none')

            $('.no_data').addClass('d-none')



            for (let i = 0; i < response.rows.length; i++) {

                let row = response.rows[i];

                $('.result_table table').append(`
                    <tr>
                    <td><a href=${"/dataset/" + row['tbiaDatasetID']} class="more" target="_blank">${gettext('查看')}</a></td>
                    <td class="datasetName">${row['name']}</td>
                    <td>${row['occurrenceCount']}</td>
                    <td>${row['datasetDateStart'] ? row['datasetDateStart'] : ''}</td>
                    <td>${row['datasetDateEnd'] ? row['datasetDateEnd'] : ''}</td>
                    <td class="rightsHolder">${gettext(row['rights_holder'])}</td>
                    <td>${row['downloadCount']}</td>
                    </tr>
                    `
                )
            }



            $('.return-num').html(response.count.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","))

            if (response.total_page > 1) {  // 判斷是否有下一頁，有才加分頁按鈕
                $('.result_table').after(
                    `<div class="page-inf">
                        <div class="page_number">
                        <a class="pre">
                            <span></span>
                        </a>
                        <a class="next">
                            <span></span>
                        </a>
                        </div>

                    </div>`)
            }

            let html = ''
            for (let i = 0; i < response.page_list.length; i++) {
                if (response.page_list[i] == response.current_page) {
                    html += `<a class="num now submitSearch" data-page="${response.page_list[i]}">${response.page_list[i]}</a>  `;
                } else {
                    html += `<a class="num submitSearch" data-page="${response.page_list[i]}">${response.page_list[i]}</a>  `
                }
            }
            $('.pre').after(html)

            // 如果有上一頁，改掉pre的onclick
            if ((response.current_page - 1) > 0) {
                $('.pre').addClass('submitSearch')
                $('.pre').data('page', response.current_page - 1)
            }
            // 如果有下一頁，改掉next的onclick
            if (response.current_page < response.total_page) {
                $('.next').addClass('submitSearch')
                $('.next').data('page', response.current_page + 1)
            }

            // 如果有前面的page list, 加上...
            if (response.current_page > 5) {
                $('.pre').after(`<a class="num bd-0 submitSearch" data-page="${response.current_page - 5}" data-from="page">...</a> `)
            }
            // 如果有後面的page list, 加上...
            if (response.page_list[response.page_list.length - 1] < response.total_page) {
                if (response.current_page + 5 > response.total_page) {
                    $('.next').before(`<a class="num bd-0 submitSearch" data-page="${response.total_page}" data-from="page">...</a> `)
                } else {
                    $('.next').before(`<a class="num bd-0 submitSearch" data-page="${response.current_page + 5}" data-from="page">...</a>`)
                }
            }

            $('.return-total-page').html(response.total_page)

            if (response.total_page > 1 && !response.page_list.includes(1)) {
                $('.pre').after('<a class="num mr-5px submitSearch" data-page="1" data-from="page">1</a>')
            }

            $('.page_number a.submitSearch').on('click', function () {
                submitSearch(is_preload=false, page=$(this).data('page'))
            })
        


        }


        $(".loading_area").addClass('d-none');
        if (!is_preload){
            $([document.documentElement, document.body]).animate({
                scrollTop: $(".sc_result").offset().top - 80
            }, 200);
        }

    })

}