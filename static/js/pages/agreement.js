$('.bt_center button').on('click', function () {
	if ($('input[name=is_authenticated]').val() == 'True') {
		if ($('input[name=policy]').is(':checked')) {
			window.location.href = '/send_sensitive_request' + window.location.search
		} else {
			alert(gettext('未勾選同意以上協議'))
		}
	} else {
		alert(gettext('請先登入'))
	}
})
