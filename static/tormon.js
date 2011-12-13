monitors = new Array();

function init_monitor(name) {

    monitors[name] = new Object();
    monitors[name].dom = $("<div/>").appendTo("body");

    $.getJSON("/data", {"name": name}, function (data) {
        monitors[name].data = data;
        update_monitor(name, []);
        poll_monitor(name);
    });
}

function poll_monitor(name) {
    $.getJSON("/poll", {"name": name}, function(data) {
        update_monitor(name, data);
    }).complete(function() {
        window.setTimeout(function () {
            poll_monitor(name);
        }, 100);
    });
}

function update_monitor(name, data) {
    var old_data = monitors[name].data;
    if (data.length < old_data.length) {
        data = old_data.slice(data.length).concat(data);
    }
    monitors[name].data = data;

    var d = new Array();

    for(i in data) {
        d.push([i, data[i]]);
    }

    $.plot(monitors[name].dom, [{
        data: d,
        lines: { show: true, fill: true }
    }]);
}

function update_list() {
    $.getJSON('/list', function (data) {
        for(var i in data) {
            if (!monitors[data[i]]) {
                init_monitor(data[i]);
            }
        }
    }).complete(function () {
        window.setTimeout(update_list, 1000);
    });
}

$(update_list);
