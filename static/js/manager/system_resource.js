
var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

function changeURL(menu) {
    history.pushState(null, '', window.location.pathname + '?' + 'menu=' + menu);
}

// 如果按上下一頁
window.onpopstate = function (e) {
    e.preventDefault();

    $('.rightbox_content').addClass('d-none')
    $('.col_menu.second_menu a').removeClass('now')
    $('.col_menu.second_menu').addClass('d-none')

    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);

    let menu = urlParams.get('menu')
    if (menu) {

        $(`a.${menu}`).addClass('now')
        $(`a.${menu}`).parent(".second_menu").slideToggle();

        $(`.rightbox_content.${menu}`).removeClass('d-none')
    }
};

(function () {

    var toolbarOptions = [
        [{ 'size': [] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'list': 'ordered' }, { 'list': 'bullet' }, { 'indent': '-1' }, { 'indent': '+1' }],
        [{ 'align': [] }],
        ['link', 'image', 'video'],
    ]

    var quill = new Quill('#editor', {
        theme: 'snow', modules: {
            'toolbar': toolbarOptions,
        }

    });

    $.ajax({
        url: `/get_link_content`,
        type: 'GET',
        success: function (response) {
            quill.pasteHTML(response.content);
        }
    });

})();

function deleteResource(resource_id) {
    $.ajax({
        type: 'POST',
        url: "/delete_resource",
        data: { 'resource_id': resource_id },
        headers: { 'X-CSRFToken': $csrf_token },
        success: function (response) {
            alert('刪除成功')
            window.location = '/manager/system/resource?menu=resource';
        }
    })
}


function loadArkTable() {
    const resourceId = $('#saveForm input[name=resource_id]').val();
    if (!resourceId) return;
    
    $.ajax({
        url: `/get_resource_ark_table?resource_id=${resourceId}`,
        type: 'GET',
        success: function(response) {
            const $table = $('.ark_table');
            $table.find('tr:not(.ark_table_header)').remove();
            
            response.rows.forEach(row => {
                const fileCell = row.file 
                    ? `<a href="${row.file.ark_href}" target="_blank">${row.file.ark}</a>` 
                    : '';
                const docCell = row.doc 
                    ? `<a href="${row.doc.ark_href}" target="_blank">${row.doc.ark}</a>` 
                    : '';
                $table.append(
                    `<tr><td>${row.version}</td><td>${row.publish_date}</td><td>${fileCell}</td><td>${docCell}</td></tr>`
                );
            });
        }
    });
}


$(document).ready(function () {

    loadArkTable();

    $('select[name=resource_type]').on('change', function () {

        $('.noticbox').addClass('d-none')

        if ($(this).find(':selected').val() == 'file') {
            $('.file_field').removeClass('d-none')
            $('.doc-link_field').removeClass('d-none')
            $('.link_field').addClass('d-none')
        } else if ($(this).find(':selected').val() == 'doc-link') {
            $('.file_field').addClass('d-none')
            $('.doc-link_field').removeClass('d-none')
            $('.link_field').addClass('d-none')
        } else {
            $('.doc-link_field').addClass('d-none')
            $('.file_field').addClass('d-none')
            $('.link_field').removeClass('d-none')
        }
    })

    $('select[name=resource_type]').trigger('change')

    // 起始頁面
    changePage(1, 'resource')

    $('.submitLink').on('click', function () {
        $('#linkForm').append(`<textarea class="d-none" name="content">${$('.ql-editor').html()}</textarea>`)
        $('#linkForm').submit()
    })

    $('.changeMenu').on('click', function () {
        let menu = $(this).data('menu');
        if (menu == 'edit') {
            $('#saveForm input[name=resource_id]').val('')
            $('#saveForm select[name=content_type]').val('strategy')
            $('#saveForm select[name=resource_type]').val('file')
            $('#saveForm input[name=file]').val('')
            $('#saveForm input[name=url]').val('')
            $('#saveForm input[name=doc_url]').val('')
            $('#preview').parent('li').html(`<span id="preview" class="d-none"></span>`)
        }

        $('.rightbox_content').addClass('d-none');
        $(`.rightbox_content.${menu}`).removeClass('d-none');
        changeURL(menu)
    })

    $('.changePage').on('click', function () {
        changePage($(this).data('page'), $(this).data('type'))
    })

    $('label[for="id_content"]').html('')

    $('#link_button').on('click', function () {
        $('.rightbox_content').addClass('d-none')
        $('.rightbox_content.edit-link').removeClass('d-none')
    })

    $('.delete_resource').on('click', function () {
        deleteResource($(this).data('resource_id'))
    })

    $('#save_resource_file').on('click', function () {
        $('.noticbox').addClass('d-none')
        var form = new FormData()
        form.append('file', $('#file')[0].files[0])

        $.ajax({
            type: 'POST',
            url: "/save_resource_file",
            data: form,
            processData: false,
            contentType: false,
            headers: { 'X-CSRFToken': $csrf_token },
            success: function (response) {
                if (response.url != null) {
                    $('#preview').html(`目前檔案：${response['filename']} <a target="_blank" href="/media/${response['url']}">(預覽)</a>`)
                    $('#preview').removeClass('d-none')
                    $('#saveForm input[name=url]').val(response['url'])
                } else {
                    $('#preview').addClass('d-none')
                    $('#saveForm input[name=url]').val('')
                }
            },
            fail: function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            }
        })
    })

    // 要確認有沒有上傳檔案 filename統一改成帶有resources/的檔名
    $('#publish').on('click', function () {
        let checked = true;

        if ($('#saveForm input[name=title]').val() == '') {
            $('#saveForm input[name=title]').next('.noticbox').removeClass('d-none')
            checked = false
        }

        if ($('#saveForm input[name=publish_date]').val() == '') {
            $('#saveForm input[name=publish_date]').next('.noticbox').removeClass('d-none')
            checked = false
        }

        // 判斷必填
        if ($('select[name=resource_type]').find(':selected').val() == 'file') {
            if ($('#saveForm .file_field input[name=url]').val() == '') {
                $('#file_error').removeClass('d-none')
                checked = false
            } else {
                url = $('#saveForm .file_field input[name=url]').val()
            }
        } else if ($('select[name=resource_type]').find(':selected').val() == 'doc-link') {

            if ($('#saveForm .doc-link_field input[name=doc_url]').val() == '') {
                checked = false
            } else {
                url = $('#saveForm .doc-link_field input[name=doc_url]').val()
            }

        } else {

            if ($('#saveForm .link_field input[name=url]').val() == '') {
                $('#link_error').removeClass('d-none')
                checked = false
            } else {
                url = $('#saveForm .link_field input[name=url]').val()
            }
        }

        if (checked) {

            const mode = $('#publish_mode').val();
            const endpoint = mode === 'new_version' ? '/publish_new_resource_version' : '/submit_resource';


            $.ajax({
                type: 'POST',
                url: endpoint,
                data: {
                    'url': url,
                    'content_type': $('#saveForm select[name=content_type]').find(":selected").val(),
                    'resource_type': $('#saveForm select[name=resource_type]').find(":selected").val(),
                    'lang': $('#saveForm select[name=resource_lang]').find(":selected").val(),
                    'resource_id': $('#saveForm input[name=resource_id]').val(),
                    'publish_date': $('#saveForm input[name=publish_date]').val(),
                    'title': $('#saveForm input[name=title]').val(),
                    'doc_url': $('#saveForm input[name=doc_url]').val(),
                    'prev_doc_url': $('#saveForm input[name=prev_doc_url]').val() || '',
                },
                headers: { 'X-CSRFToken': $csrf_token },
                success: function (response) {
                    if (response.success) {
                        window.location = '/manager/system/resource?menu=resource';
                    } else {
                        alert('儲存失敗：' + (response.error || '未知錯誤'));
                    }
                },
                error: function (xhr) {
                    let msg = '儲存失敗，請聯絡管理員';
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        msg = '儲存失敗：' + xhr.responseJSON.error;
                    }
                    alert(msg);
                }
            })

        } else {
            alert('請檢查內容是否完整！')
        }
    })

    $(`a.${$('input[name=menu]').val()}`).addClass('now')
    $(`a.${$('input[name=menu]').val()}`).parent(".second_menu").slideToggle();
    $(`.rightbox_content.${$('input[name=menu]').val()}`).removeClass('d-none')

    $(".mb_fixed_btn").on("click", function (event) {
        $(".mbmove").toggleClass("open");
        $(this).toggleClass("now");
    });

    $(".rd_click").on("click", function (event) {
        $(".rd_click").closest("li").removeClass("now");
        $(this).closest("li").toggleClass("now");
        $(this).closest("li").find(".second_menu").slideToggle();
    });


    $(".second_menu a").on("click", function (event) {
        $(this).parent().parent().parent('ul').children('li.now').removeClass("now");
        $(".second_menu a").removeClass("now");
        $(this).addClass("now")
        $(this).parent().parent('li').addClass('now')
    });

    $('#publish_ark_version').on('click', function () {
        if (!confirm('確定要發布新版本嗎？發布後目前版本將無法再修改')) return;
        
        $('#publish_mode').val('new_version');
        // 清掉檔案 url，強制重新上傳（其他欄位本來就 enabled）
        $('#saveForm input[name=url]').val('');
        $('#preview').addClass('d-none');
        
        $('#new_version_banner .noticbox').removeClass('d-none');
        $(this).addClass('d-none');
        $('#cancel_new_version').removeClass('d-none');
    });

    $('#cancel_new_version').on('click', function () {
        location.reload();
    });


})

function changePage(page, menu) {
    $.ajax({
        url: `/change_manager_page?page=${page}&menu=${menu}`,
        type: 'GET',
        success: function (response) {

            // 保留表格 header 修改表格內容
            $(`.${menu}_table tr:not(.${menu}_table_header)`).remove()
            $(`.${menu}_table`).append(`${response.data}`)
            $(`.${menu}_table`).parent().next('.page_number').remove()

            // 修改頁碼
            if (response.total_page > 0) {
                $(`.${menu}_table`).parent().after(
                    `<div class="page_number">
                    <a class="num changePage" data-page="1" data-type="${menu}">1</a>
                    <a class="pre"><span></span>上一頁</a>  
                    <a class="next">下一頁<span></span></a>
                    <a class="num changePage" data-page="${response.total_page}" data-type="${menu}">${response.total_page}</a>
                    </div>`)

                let html = ''
                for (let i = 0; i < response.page_list.length; i++) {
                    if (response.page_list[i] == response.current_page) {
                        html += ` <a class="num now changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `;
                    } else {
                        html += ` <a class="num changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `
                    }
                }

                $(`.${menu} .item .page_number a.pre`).after(html)

                // 如果有下一頁，改掉next的onclick
                if (response.current_page < response.total_page) {
                    $(`.${menu} .item .page_number a.next`).addClass('changePage');
                    $(`.${menu} .item .page_number a.next`).data('page', response.current_page + 1);
                    $(`.${menu} .item .page_number a.next`).data('type', menu);
                } else {
                    $(`.${menu} .item .page_number a.next`).addClass('pt-none')
                }

                // 如果有上一頁，改掉prev的onclick
                if (response.current_page - 1 > 0) {
                    $(`.${menu} .item .page_number a.pre`).addClass('changePage');
                    $(`.${menu} .item .page_number a.pre`).data('page', response.current_page - 1);
                    $(`.${menu} .item .page_number a.pre`).data('type', menu);
                } else {
                    $(`.${menu} .item .page_number a.pre`).addClass('pt-none')
                }

                $('.changePage').off('click')
                $('.changePage').on('click', function () {
                    changePage($(this).data('page'), $(this).data('type'))
                })

                $('.delete_resource').off('click')
                $('.delete_resource').on('click', function () {
                    deleteResource($(this).data('resource_id'))
                })
            }
        }
    });

}