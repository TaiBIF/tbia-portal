$(document).ready(function () {

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

  $('.updateKeyword').on('click', function () {
    $('.noticbox').addClass('d-none')

    let checked = true;

    if (!$('input[name=keyword_1]').val()) {
      $('input[name=keyword_1]').next('.noticbox').removeClass('d-none')
      checked = false
    }
    if (!$('input[name=keyword_2]').val()) {
      $('input[name=keyword_2]').next('.noticbox').removeClass('d-none')
      checked = false
    }
    if (!$('input[name=keyword_3]').val()) {
      $('input[name=keyword_3]').next('.noticbox').removeClass('d-none')
      checked = false
    }

    if (!$('input[name=keyword_en_1]').val()) {
      $('input[name=keyword_en_1]').next('.noticbox').removeClass('d-none')
      checked = false
    }
    if (!$('input[name=keyword_en_2]').val()) {
      $('input[name=keyword_en_2]').next('.noticbox').removeClass('d-none')
      checked = false
    }
    if (!$('input[name=keyword_en_3]').val()) {
      $('input[name=keyword_en_3]').next('.noticbox').removeClass('d-none')
      checked = false
    }


    if (checked) {
      $.ajax({
        url: "/update_keywords",
        data: $('#keywordForm').serialize(),
        type: 'POST',
        dataType: 'json',
      })
        .done(function (response) {
          if (response.status == 'success') {
            alert('修改成功')
          }

        })
        .fail(function (xhr, status, errorThrown) {
          alert(gettext('發生未知錯誤！請聯絡管理員'))

          console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })
    }

  })

})

