/*
Copyright (C) Philippe Meyer 2019-2021
Distributed under the MIT License 

vanillaSelectBox : v1.05 : setValue() bug correction on single mode. You could not set the value
vanillaSelectBox : v1.04 : select all issue fixed by https://github.com/arthur911016 
vanillaSelectBox : v1.03 : getResult() an new fonction to get the selected values in an array
vanillaSelectBox : v1.02 : Adding 2 new options "itemsSeparator" to change the default "," item separator showing in the button and translations.item to show the item in singular if there is only one.
vanillaSelectBox : v1.01 : Removing useless code line 550,551 issue 71 by chchch
vanillaSelectBox : v1.00 : Adding a package.json file 
vanillaSelectBox : v0.78 : Stop using inline styles in the main button. You can steal use keepInlineStyles:true to use the legacy behaviour
vanillaSelectBox : v0.77 : Work on place holder with bastoune help => still seems to lose placeholder value on multiple dropdown checkall
vanillaSelectBox : v0.76 : New changeTree function : to rebuild the original tree with new data + correcting empty() function
vanillaSelectBox : v0.75 : Remote search ready + local search modification : when a check on optgroup checks children only 
                           if they not excluded from search.
vanillaSelectBox : v0.72 : Remote search (WIP) bugfix [x] Select all duplicated
vanillaSelectBox : v0.71 : Remote search (WIP) better code
vanillaSelectBox : v0.70 : Remote search (WIP) for users to test
vanillaSelectBox : v0.65 : Two levels: bug fix : groups are checked/unchecked when check all/uncheck all is clicked
vanillaSelectBox : v0.64 : Two levels: groups are now checkable to check/uncheck the children options 
vanillaSelectBox : v0.63 : Two levels: one click on the group selects / unselects children
vanillaSelectBox : v0.62 : New option: maxOptionWidth set a maximum width for each option for narrow menus
vanillaSelectBox : v0.61 : New option: maxSelect, set a maximum to the selectable options in a multiple choice menu
vanillaSelectBox : v0.60 : Two levels: Optgroups are now used to show two level dropdowns 
vanillaSelectBox : v0.59 : Bug fix : search box was overlapping first item in single selects
vanillaSelectBox : v0.58 : Bug fixes
vanillaSelectBox : v0.57 : Bug fix (minWidth option not honored)
vanillaSelectBox : v0.56 : The multiselect checkboxes are a little smaller, maxWidth option is now working + added minWidth option as well
                           The button has now a style attribute to protect its appearance 
vanillaSelectBox : v0.55 : All attributes from the original select options are copied to the selectBox element
vanillaSelectBox : v0.54 : if all the options of the select are selected by the user then the check all checkbox is checked
vanillaSelectBox : v0.53 : if all the options of the select are selected then the check all checkbox is checked
vanillaSelectBox : v0.52 : Better support of select('all') => command is consistent with checkbox and selecting / deselecting while searching select / uncheck only the found items
vanillaSelectBox : v0.51 : Translations for select all/clear all + minor css corrections + don't select disabled items
vanillaSelectBox : v0.50 : PR by jaguerra2017 adding a select all/clear all check button + optgroup support !
vanillaSelectBox : v0.41 : Bug corrected, the menu content was misplaced if a css transform was applied on a parent
vanillaSelectBox : v0.40 : A click on one selectBox close the other opened boxes
vanillaSelectBox : v0.35 : You can enable and disable items
vanillaSelectBox : v0.30 : The menu stops moving around on window resize and scroll + z-index in order of creation for multiple instances
vanillaSelectBox : v0.26 : Corrected bug in stayOpen mode with disable() function
vanillaSelectBox : v0.25 : New option stayOpen, and the dropbox is no longer a dropbox but a nice multi-select
previous version : v0.24 : corrected bug affecting options with more than one class
https://github.com/PhilippeMarcMeyer/vanillaSelectBox
*/


let var_dict = {
    '刺': '[刺刺]', '刺': '[刺刺]', '葉': '[葉葉]', '葉': '[葉葉]',
    '鈎': '[鈎鉤]', '鉤': '[鈎鉤]', '臺': '[臺台]', '台': '[臺台]', '螺': '[螺螺]', '螺': '[螺螺]', '羣': '[群羣]', '群': '[群羣]', '峯': '[峯峰]', '峰': '[峯峰]', '曬': '[晒曬]', '晒': '[晒曬]', '裏': '[裏裡]', '裡': '[裏裡]', '薦': '[荐薦]', '荐': '[荐薦]', '艷': '[豔艷]', '豔': '[豔艷]', '粧': '[妝粧]', '妝': '[妝粧]', '濕': '[溼濕]', '溼': '[溼濕]', '樑': '[梁樑]', '梁': '[梁樑]', '秘': '[祕秘]', '祕': '[祕秘]', '污': '[汙污]', '汙': '[汙污]', '册': '[冊册]', '冊': '[冊册]', '唇': '[脣唇]', '脣': '[脣唇]', '朶': '[朵朶]', '朵': '[朵朶]', '鷄': '[雞鷄]', '雞': '[雞鷄]', '猫': '[貓猫]', '貓': '[貓猫]', '踪': '[蹤踪]', '蹤': '[蹤踪]', '恒': '[恆恒]', '恆': '[恆恒]', '獾': '[貛獾]', '貛': '[貛獾]', '万': '[萬万]', '萬': '[萬万]', '两': '[兩两]', '兩': '[兩两]', '椮': '[槮椮]', '槮': '[槮椮]', '体': '[體体]', '體': '[體体]', '鳗': '[鰻鳗]', '鰻': '[鰻鳗]', '蝨': '[虱蝨]', '虱': '[虱蝨]', '鲹': '[鰺鲹]', '鰺': '[鰺鯵]', '鳞': '[鱗鳞]', '鱗': '[鱗鳞]', '鳊': '[鯿鳊]', '鯿': '[鯿鳊]', '鯵': '[鰺鯵]', '鲨': '[鯊鲨]', '鯊': '[鯊鲨]', '鹮': '[䴉鹮]', '䴉': '[䴉鹮]', '鴴': '(行鳥|鴴)', '鵐': '(鵐|巫鳥)', '䱵': '(䱵|魚翁)', '䲗': '(䲗|魚銜)', '䱀': '(䱀|魚央)', '䳭': '(䳭|即鳥)', '鱼': '[魚鱼]', '魚': '[魚鱼]', '鹨': '[鷚鹨]', '鷚': '[鷚鹨]', '蓟': '[薊蓟]', '薊': '[薊蓟]', '黒': '[黑黒]', '黑': '[黑黒]', '隠': '[隱隠]', '隱': '[隱隠]', '黄': '[黃黄]', '黃': '[黃黄]', '囓': '[嚙囓]', '嚙': '[嚙囓]', '莨': '[茛莨]', '茛': '[茛莨]', '霉': '[黴霉]', '黴': '[黴霉]', '莓': '[苺莓]', '苺': '[苺莓]', '藥': '[葯藥]', '葯': '[葯藥]', '菫': '[堇菫]', '堇': '[堇菫]',}
let var2_dict = {'行鳥': '(行鳥|鴴)', '蝦虎': '[鰕蝦]虎', '鰕虎': '[鰕蝦]虎', '巫鳥': '(鵐|巫鳥)', '魚翁': '(䱵|魚翁)', '魚銜': '(䲗|魚銜)', '魚央': '(䱀|魚央)', '游蛇': '[遊游]蛇', '遊蛇': '[遊游]蛇', '即鳥': '(䳭|即鳥)', '椿象': '[蝽椿]象', '蝽象': '[蝽椿]象'}

function getVariants(text){
    let new_string = '';
    // 單個異體字
    for (t of text){
        if (Object.keys(var_dict).indexOf(t) != -1) {
            new_string += var_dict[t]
        } else {
            new_string += t
        }
    } 

    // 兩個異體字
    for (k of Object.keys(var2_dict)){
        if (new_string.includes(k)){
            new_string = new_string.replace(k, var2_dict[k]);
        }
    }

    return new_string
}

function escapeRegExp(text) {
    return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
}

let VSBoxCounter = function () {
    let count = 0;
    let instances = [];
    return {
        set: function (instancePtr) {
            instances.push({ offset: ++count, ptr: instancePtr });
            return instances[instances.length - 1].offset;
        },
        remove: function (instanceNr) {
            let temp = instances.filter(function (x) {
                return x.offset != instanceNr;
            })
            instances = temp.splice(0);
        },
        closeAllButMe: function (instanceNr) {
            instances.forEach(function (x) {
                if (x.offset != instanceNr) {
                    x.ptr.closeOrder();
                }
            });
        }
    };
}();

function vanillaSelectBox(domSelector, options) {
    let self = this;
    this.instanceOffset = VSBoxCounter.set(self);
    this.domSelector = domSelector;
    this.root = document.querySelector(domSelector);
    this.rootToken = null;
    this.main;
    this.button;
    this.title;
    this.isMultiple = this.root.hasAttribute("multiple");
    this.multipleSize = this.isMultiple && this.root.hasAttribute("size") ? parseInt(this.root.getAttribute("size")) : -1;
    this.isOptgroups = false;
    this.currentOptgroup = 0;
    this.drop;
    this.top;
    this.left;
    this.options;
    this.listElements;
    this.isDisabled = false;
    this.search = false;
    this.searchZone = null;
    this.inputBox = null;
    this.disabledItems = [];
    /*this.ulminWidth = 140;*/
    this.ulmaxWidth = "100%";
    this.ulminHeight = 25;
    this.maxOptionWidth = Infinity;
    this.maxSelect = Infinity;
    this.isInitRemote = false;
    this.isSearchRemote = false;
    this.onInit = null;
    this.onSearch = null; // if isRemote is true : a user defined function that loads more options from the back
    this.onInitSize = null;
    this.forbidenAttributes = ["class", "selected", "disabled", "data-text", "data-value", "style"];
    this.forbidenClasses = ["active", "disabled"];
    this.userOptions = {
        maxWidth: "100%",
        minWidth: -1,
        maxHeight: 300,
        translations: { "all": "All", "item": "item","items": "items", "selectAll": "Select All", "clearAll": "Clear All" },
        search: false,
        placeHolder: "",
        stayOpen: false,
        disableSelectAll: false,
        buttonItemsSeparator : ","
    }
    this.keepInlineStyles = true;
    this.keepInlineCaretStyles = true;
    if (options) {
        if(options.itemsSeparator!= undefined){
            this.userOptions.buttonItemsSeparator = options.itemsSeparator;
        }
        if (options.maxWidth != undefined) {
            this.userOptions.maxWidth = options.maxWidth;
        }
        if (options.minWidth != undefined) {
            this.userOptions.minWidth = options.minWidth;
        }
        if (options.maxHeight != undefined) {
            this.userOptions.maxHeight = options.maxHeight;
        }
        if (options.translations != undefined) {
            for (var property in options.translations) {
                if (options.translations.hasOwnProperty(property)) {
                    if (this.userOptions.translations[property]) {
                        this.userOptions.translations[property] = options.translations[property];
                    }
                }
            }
        }
        if (options.placeHolder != undefined) {
            this.userOptions.placeHolder = options.placeHolder;
        }
        if (options.search != undefined) {
            this.search = options.search;
        }
        if (options.remote != undefined && options.remote) {

           // user defined onInit  function
            if (options.remote.onInit!= undefined && typeof options.remote.onInit === 'function') {
                this.onInit = options.remote.onInit;
                this.isInitRemote = true;
            } 
            if (options.remote.onInitSize != undefined) {
                this.onInitSize = options.remote.onInitSize;
                if (this.onInitSize < 3) this.onInitSize = 3;
            }
            // user defined remote search function
            if (options.remote.onSearch != undefined && typeof options.remote.onSearch === 'function') {
                this.onSearch = options.remote.onSearch;
                this.isSearchRemote = true;
            }
        }

        if (options.stayOpen != undefined) {
            this.userOptions.stayOpen = options.stayOpen;
        }

        if (options.disableSelectAll != undefined) {
            this.userOptions.disableSelectAll = options.disableSelectAll;
        }

        if (options.maxSelect != undefined && !isNaN(options.maxSelect) && options.maxSelect >= 1) {
            this.maxSelect = options.maxSelect;
            this.userOptions.disableSelectAll = true;
        }

        if (options.maxOptionWidth != undefined && !isNaN(options.maxOptionWidth) && options.maxOptionWidth >= 20) {
            this.maxOptionWidth = options.maxOptionWidth;
            this.ulminWidth = options.maxOptionWidth + 60;
            this.ulmaxWidth = options.maxOptionWidth + 60;
        }

        if(options.keepInlineStyles != undefined ) {
            this.keepInlineStyles = options.keepInlineStyles;
        }
        if(options.keepInlineCaretStyles != undefined ) {
            this.keepInlineCaretStyles = options.keepInlineCaretStyles;
        }
        
    }

    this.closeOrder = function () {
        let self = this;
        if (!self.userOptions.stayOpen) {
            self.drop.style.visibility = "hidden";
            if (self.search) {
                self.inputBox.value = "";
                Array.prototype.slice.call(self.listElements).forEach(function (x) {
                    x.classList.remove("hide");
                });
            }
        }
    }

    this.getCssArray = function (selector) {
        // Why inline css ? To protect the button display from foreign css files
        let cssArray = [];
        if (selector === ".vsb-main button") {
            cssArray = [
                { "key": "min-width", "value": "120px" },
                { "key": "border-radius", "value": "0" },
                { "key": "width", "value": "100%" },
                { "key": "text-align", "value": "left" },
                { "key": "z-index", "value": "1" },
                { "key": "color", "value": "#333" },
                { "key": "background", "value": "white !important" },
                { "key": "border", "value": "1px solid #999 !important" },
                { "key": "line-height", "value": "20px" },
                { "key": "font-size", "value": "14px" },
                { "key": "padding", "value": "6px 12px" }
            ]
        }

        return cssArrayToString(cssArray);

        function cssArrayToString(cssList) {
            let list = "";
            cssList.forEach(function (x) {
                list += x.key + ":" + x.value + ";";
            });
            return list;
        }
    }

    this.init = function () {
        let self = this;
        if (self.isInitRemote) {
            self.onInit("",self.onInitSize)
                .then(function (data) {
                    self.buildSelect(data);
                    self.createTree();
                    if (self.domSelector=='#higherTaxa'){
                        if (data.length>1){
                            self.setValue(data[1]['value'])
                            window.higherTaxaInit = true
                        } else {
                            window.higherTaxaInit = true
                        }
                    } else if (self.domSelector=='#locality') {
                        window.localityInit = true
                    }
                    // 確定兩邊都init完成後才觸發changeAction
                    if( window.localityInit == true & window.higherTaxaInit == true) {
                        changeAction()
                    }
                });
        } else {
            self.createTree();
        }
    }

    this.getResult = function () {
        let self = this;
        let result = [];
        let collection = self.root.querySelectorAll("option");
        collection.forEach(function (x) {
            if (x.selected) {
                result.push(x.value);
            }
        });
        return result;
    }

    this.createTree = function () {

        this.rootToken = self.domSelector.replace(/[^A-Za-z0-9]+/, "")
        this.root.style.display = "none";
        let already = document.getElementById("btn-group-" + this.rootToken);
        if (already) {
            already.remove();
        }
        this.main = document.createElement("div");
        this.root.parentNode.insertBefore(this.main, this.root.nextSibling);
        this.main.classList.add("vsb-main");
        this.main.setAttribute("id", "btn-group-" + this.rootToken);
        this.main.style.marginLeft = this.main.style.marginLeft;
        if (self.userOptions.stayOpen) {
            this.main.style.minHeight = (this.userOptions.maxHeight + 10) + "px";
        }

        if (self.userOptions.stayOpen) {
            this.button = document.createElement("div");
        } else {
            this.button = document.createElement("button");
            if(this.keepInlineStyles) {
                var cssList = self.getCssArray(".vsb-main button");
                this.button.setAttribute("style", cssList);
            }
        }
        this.button.style.maxWidth = this.userOptions.maxWidth + "px";
        if (this.userOptions.minWidth !== -1) {
            this.button.style.minWidth = this.userOptions.minWidth + "px";
        }

        this.main.appendChild(this.button);
        this.title = document.createElement("span");
        this.button.appendChild(this.title);
        this.title.classList.add("title");
        let caret = document.createElement("span");
        this.button.appendChild(caret);

        caret.classList.add("caret");
        if(this.keepInlineCaretStyles) {
            caret.style.position = "absolute";
            caret.style.right = "8px";
            caret.style.marginTop = "8px";
        }

        if (self.userOptions.stayOpen) {
            caret.style.display = "none";
            this.title.style.paddingLeft = "20px";
            this.title.style.fontStyle = "italic";
            this.title.style.verticalAlign = "20%";
        }

        this.drop = document.createElement("div");
        this.main.appendChild(this.drop);
        this.drop.classList.add("vsb-menu");
        this.drop.style.zIndex = 2000 - this.instanceOffset;
        this.ul = document.createElement("ul");
        this.drop.appendChild(this.ul);

        this.ul.style.maxHeight = this.userOptions.maxHeight + "px";
        this.ul.style.minWidth = this.ulminWidth + "px";
        this.ul.style.maxWidth = this.ulmaxWidth + "px";
        this.ul.style.minHeight = this.ulminHeight + "px";
        if (this.isMultiple) {
            this.ul.classList.add("multi");
            if (!self.userOptions.disableSelectAll) {
                let selectAll = document.createElement("option");
                selectAll.setAttribute("value", 'all');
                selectAll.innerText = self.userOptions.translations.selectAll;
                this.root.insertBefore(selectAll, (this.root.hasChildNodes())
                    ? this.root.childNodes[0]
                    : null);
            }
        }
        let selectedTexts = ""
        let sep = "";
        let nrActives = 0;

        if (this.search) {
            this.searchZone = document.createElement("div");
            this.ul.appendChild(this.searchZone);
            this.searchZone.classList.add("vsb-js-search-zone");
            this.searchZone.style.zIndex = 2001 - this.instanceOffset;
            this.inputBox = document.createElement("input");
            this.searchZone.appendChild(this.inputBox);
            this.inputBox.setAttribute("type", "text");
            this.inputBox.setAttribute("id", "search_" + this.rootToken);
            if (this.maxOptionWidth < Infinity) {
                this.searchZone.style.maxWidth = self.maxOptionWidth + 30 + "px";
                this.inputBox.style.maxWidth = self.maxOptionWidth + 30 + "px";

            }
            
            var para = document.createElement("p");
            this.ul.appendChild(para);
            para.style.fontSize = "12px";
            para.innerHTML = "&nbsp;";
            this.ul.addEventListener("scroll", function (e) {
                var y = this.scrollTop;
                //self.searchZone.parentNode.style.top = y + "px";
            });
        }

        this.options = document.querySelectorAll(this.domSelector + " > option");
        Array.prototype.slice.call(this.options).forEach(function (x) {
            let text = x.textContent;
            let value = x.value;
            let originalAttrs;
            if (x.hasAttributes()) {
                originalAttrs = Array.prototype.slice.call(x.attributes)
                    .filter(function (a) {
                        return self.forbidenAttributes.indexOf(a.name) === -1
                    });
            }
            let classes = x.getAttribute("class");
            if (classes) {
                classes = classes
                    .split(" ")
                    .filter(function (c) {
                        return self.forbidenClasses.indexOf(c) === -1
                    });
            } else {
                classes = [];
            }
            let li = document.createElement("li");
            let isSelected = x.hasAttribute("selected");
            let isDisabled = x.hasAttribute("disabled");

            self.ul.appendChild(li);
            li.setAttribute("data-value", value);
            li.setAttribute("data-text", text);

            if (originalAttrs !== undefined) {
                originalAttrs.forEach(function (a) {
                    li.setAttribute(a.name, a.value);
                });
            }

            classes.forEach(function (x) {
                li.classList.add(x);
            });

            if (self.maxOptionWidth < Infinity) {
                li.classList.add("short");
                li.style.maxWidth = self.maxOptionWidth + "px";
            }

            if (isSelected) {
                nrActives++;
                selectedTexts += sep + text;
                sep = self.userOptions.buttonItemsSeparator;
                li.classList.add("active");
                if (!self.isMultiple) {
                    self.title.textContent = text;
                    if (classes.length != 0) {
                        classes.forEach(function (x) {
                            self.title.classList.add(x);
                        });
                    }
                }
            }
            if (isDisabled) {
                li.classList.add("disabled");
            }
            li.appendChild(document.createTextNode(" " + text));
        });

        if (document.querySelector(self.domSelector + ' optgroup') !== null) {
            self.isOptgroups = true;
            self.options = document.querySelectorAll(self.domSelector + " option");
            let groups = document.querySelectorAll(self.domSelector + ' optgroup');
            Array.prototype.slice.call(groups).forEach(function (group) {
                let groupOptions = group.querySelectorAll('option');
                let li = document.createElement("li");
                let span = document.createElement("span");
                let iCheck = document.createElement("i");
                let labelElement = document.createElement("b");
                let dataWay = group.getAttribute("data-way");
                if (!dataWay) dataWay = "closed";
                if (!dataWay || (dataWay !== "closed" && dataWay !== "open")) dataWay = "closed";
                li.appendChild(span);
                li.appendChild(iCheck);
                self.ul.appendChild(li);
                li.classList.add('grouped-option');
                li.classList.add(dataWay);
                self.currentOptgroup++;
                let optId = self.rootToken + "-opt-" + self.currentOptgroup;
                li.id = optId;
                li.appendChild(labelElement);
                labelElement.appendChild(document.createTextNode(group.label));
                li.setAttribute("data-text", group.label);
                self.ul.appendChild(li);

                Array.prototype.slice.call(groupOptions).forEach(function (x) {
                    let text = x.textContent;
                    let value = x.value;
                    let classes = x.getAttribute("class");
                    if (classes) {
                        classes = classes.split(" ");
                    }
                    else {
                        classes = [];
                    }
                    classes.push(dataWay);
                    let li = document.createElement("li");
                    let isSelected = x.hasAttribute("selected");
                    self.ul.appendChild(li);
                    li.setAttribute("data-value", value);
                    li.setAttribute("data-text", text);
                    li.setAttribute("data-parent", optId);
                    if (classes.length != 0) {
                        classes.forEach(function (x) {
                            li.classList.add(x);
                        });
                    }
                    if (isSelected) {
                        nrActives++;
                        selectedTexts += sep + text;
                        sep = self.userOptions.buttonItemsSeparator;
                        li.classList.add("active");
                        if (!self.isMultiple) {
                            self.title.textContent = text;
                            if (classes.length != 0) {
                                classes.forEach(function (x) {
                                    self.title.classList.add(x);
                                });
                            }
                        }
                    }
                    li.appendChild(document.createTextNode(text));
                })
            })
        }

        let optionsLength = self.options.length - Number(!self.userOptions.disableSelectAll);

        // 不要顯示全部 都顯示選了幾個選項
        /*if (optionsLength == nrActives) { // Bastoune idea to preserve the placeholder
            let wordForAll = self.userOptions.translations.all;
            selectedTexts = wordForAll;
        } else */ 
        
        if (self.multipleSize != -1) {
            if (nrActives > self.multipleSize) {
                let wordForItems = nrActives === 1 ? self.userOptions.translations.item : self.userOptions.translations.items;
                selectedTexts = nrActives + " " + wordForItems;
            }
        }
        if (self.isMultiple) {
            self.title.innerHTML = selectedTexts;
        }
        if (self.userOptions.placeHolder != "" && self.title.textContent == "") {
            self.title.textContent = self.userOptions.placeHolder;
        }
        self.listElements = self.drop.querySelectorAll("li:not(.grouped-option)");
        if (self.search) {
            self.inputBox.addEventListener("keyup", function (e) {
                if ( !e.isComposing ){ // 注音輸入完成才搜尋
                    let searchValue = e.target.value.toUpperCase();
                    let searchValueLength = searchValue.length;
                    let nrFound = 0;
                    let nrChecked = 0;
                    let selectAll = null;
                    if (self.isSearchRemote) {
                        if (searchValueLength == 0) {
                            self.remoteSearchIntegrate(null);
                        } else if (searchValueLength >= 1) {
                            self.onSearch(searchValue)
                                .then(function (data) {
                                    self.remoteSearchIntegrate(data);
                                });
                            e.stopPropagation()
                            e.preventDefault();
                        }
                    } else {
                        if (searchValueLength < 1) {
                            Array.prototype.slice.call(self.listElements).forEach(function (x) {
                                if (x.getAttribute('data-value') === 'all') {
                                    selectAll = x;
                                } else {
                                    x.classList.remove("hidden-search");
                                    nrFound++;
                                    nrChecked += x.classList.contains('active');
                                }
                            });
                        } else {
                            Array.prototype.slice.call(self.listElements).forEach(function (x) {
                                if (x.getAttribute('data-value') !== 'all') {
                                    let text = x.getAttribute("data-text").toUpperCase();
                                    if (text.slice(searchValue).search(getVariants(escapeRegExp(searchValue))) === -1 && x.getAttribute('data-value') !== 'all') {
                                        x.classList.add("hidden-search");
                                    } else {
                                        nrFound++;
                                        x.classList.remove("hidden-search");
                                        nrChecked += x.classList.contains('active');
                                    }
                                } else {
                                    selectAll = x;
                                }
                            });
                        }
                        if (selectAll) {
                            if (nrFound === 0) {
                                selectAll.classList.add('disabled');
                            } else {
                                selectAll.classList.remove('disabled');
                            }
                            if (nrChecked !== nrFound) {
                                selectAll.classList.remove("active");
                                selectAll.innerText = self.userOptions.translations.selectAll;
                                selectAll.setAttribute('data-selected', 'false')
                            } else {
                                selectAll.classList.add("active");
                                selectAll.innerText = self.userOptions.translations.clearAll;
                                selectAll.setAttribute('data-selected', 'true')
                            }
                        }
                    }
                }
            }); 
        }

        if (self.userOptions.stayOpen) {
            self.drop.style.visibility = "visible";
            self.drop.style.boxShadow = "none";
            self.drop.style.minHeight = (this.userOptions.maxHeight + 10) + "px";
            self.drop.style.position = "relative";
            self.drop.style.left = "0px";
            self.drop.style.top = "0px";
            self.button.style.border = "none";
        } else {

            this.button.addEventListener("click", function (e) {
                if (e.pointerType != ''){
                    if (self.isDisabled) return;
                    if (self.drop.style.visibility == "visible") {
                        self.drop.style.visibility = 'hidden'
                    } else {
                        self.drop.style.visibility = "visible";
                        // 只處理資料集 & 出現地             
                        if (self.domSelector=='#datasetName'|self.domSelector=='#locality'){
                            let selected_value = self.getResult()
                            if (selected_value.length > 0){ 
                                // 拿掉search zone
                                self.ul.removeChild(self.ul.firstChild)
                                // 拿掉para
                                self.ul.removeChild(self.ul.firstChild)

                                for (let i = 0; i < self.listElements.length; i++) {
                                    if(self.listElements[i].className=='active'& self.listElements[i].innerText!='全選'){
                                        self.ul.prepend(self.listElements[i])
                                    }
                                }

                                var para = document.createElement("p");
                                self.ul.prepend(para);
                                para.style.fontSize = "12px";
                                para.innerHTML = "&nbsp;";          
                                self.ul.prepend(self.searchZone)

                                self.ul.scrollTop = "0px";
                                self.ul.style.top = "0px";
                    
                            }
                        }

                    }
                
                    document.addEventListener("click", function(e){
                        document.removeEventListener("click", docListener);
                        if (self.search) {
                            self.inputBox.value = "";
                            Array.prototype.slice.call(self.listElements).forEach(function (x) {
                                x.classList.remove("hidden-search");
                            });
                        } 
                        
                        // 如果按其他地方則關閉dropdown 除了按search zone & 全選
                        if (e.target.id!='search_locality' & e.target.id!='search_datasetName' & e.target.id!='search_rightsHolder' & e.target.id!='search_higherTaxa' & e.target.dataset.text!='全選'){
                            self.drop.style.visibility = "hidden";
                        }
                    });
                    e.preventDefault();
                    e.stopPropagation();
                    if (!self.userOptions.stayOpen) {
                        VSBoxCounter.closeAllButMe(self.instanceOffset);
                    }
                }
            });
        }

        this.drop.addEventListener("click", function (e) {
            if (self.isDisabled) return;
            if (e.target.tagName === 'INPUT') return;
            let isShowHideCommand = e.target.tagName === 'SPAN';
            let isCheckCommand = e.target.tagName === 'I';
            let liClicked = e.target.parentElement;
            if (!liClicked.hasAttribute("data-value")) {
                if (liClicked.classList.contains("grouped-option")) {
                    if (!isShowHideCommand && !isCheckCommand) return;
                    let oldClass, newClass;
                    if (isCheckCommand) { // check or uncheck children
                        self.checkUncheckFromParent(liClicked);
                    } else { //open or close
                        if (liClicked.classList.contains("open")) {
                            oldClass = "open"
                            newClass = "closed"
                        } else {
                            oldClass = "closed"
                            newClass = "open"
                        }
                        liClicked.classList.remove(oldClass);
                        liClicked.classList.add(newClass);
                        let theChildren = self.drop.querySelectorAll("[data-parent='" + liClicked.id + "']");
                        theChildren.forEach(function (x) {
                            x.classList.remove(oldClass);
                            x.classList.add(newClass);
                        })
                    }
                    return;
                }
            }
            let choiceValue = e.target.getAttribute("data-value");
            let choiceText = e.target.getAttribute("data-text");
            let className = e.target.getAttribute("class");

            if (className && className.indexOf("disabled") != -1) {
                return;
            }

            if (className && className.indexOf("overflow") != -1) {
                return;
            }

            if (choiceValue === 'all') {
                if (e.target.hasAttribute('data-selected')
                    && e.target.getAttribute('data-selected') === 'true') {
                    self.setValue('none')
                } else {
                    self.setValue('all');
                }
                return;
            }

            if (!self.isMultiple) {
                self.root.value = choiceValue;
                self.title.textContent = choiceText;
                self.listElements = self.drop.querySelectorAll("li:not(.grouped-option)");
                self.title.setAttribute("class", "title");
                /*
                if (className) {
                    self.title.setAttribute("class", className + " title");
                } else {
                    self.title.setAttribute("class", "title");
                }*/
                Array.prototype.slice.call(self.listElements).forEach(function (x) {
                    x.classList.remove("active");
                });
                if (choiceValue != "") {
                    e.target.classList.add("active");
                }
                self.privateSendChange();
                if (!self.userOptions.stayOpen) {
                    docListener();
                }
            } else {
                // 如果有任何的更動 把preselect拿掉
                window.has_par = false

                let wasActive = false;
                if (className) {
                    wasActive = className.indexOf("active") != -1;
                }
                if (wasActive) {
                    e.target.classList.remove("active");
                } else {
                    e.target.classList.add("active");
                }
                if (e.target.hasAttribute("data-parent")) {
                    self.checkUncheckFromChild(e.target);
                }

                let selectedTexts = ""
                let sep = "";
                let nrActives = 0;
                let nrAll = 0;
                for (let i = 0; i < self.options.length; i++) {
                    nrAll++;
                    if (self.options[i].value == choiceValue) {
                        self.options[i].selected = !wasActive;
                    }
                    if (self.options[i].selected) {
                        nrActives++;
                        selectedTexts += sep + self.options[i].textContent;
                        sep = self.userOptions.buttonItemsSeparator;
                    }
                }
                /*
                if (nrAll == nrActives - Number(!self.userOptions.disableSelectAll)) {
                    let wordForAll = self.userOptions.translations.all;
                    selectedTexts = wordForAll;
                } else */
                
                if (self.multipleSize != -1) {
                    if (nrActives > self.multipleSize) {
                        let wordForItems = nrActives === 1 ? self.userOptions.translations.item : self.userOptions.translations.items;
                        selectedTexts = nrActives + " " + wordForItems;
                    }
                }
                self.title.textContent = selectedTexts;
                self.checkSelectMax(nrActives);
                self.checkUncheckAll();
                self.privateSendChange();
                multiple_click = true
            }
            e.preventDefault();
            e.stopPropagation();
            if (self.userOptions.placeHolder != "" && (self.title.textContent == "--重設--"|self.title.textContent == "--不限--"|self.title.textContent == "")) {
                self.title.textContent = self.userOptions.placeHolder;
            }
        });
        function docListener() {
            document.removeEventListener("click", docListener);
            if (self.search) {
                self.inputBox.value = "";
                Array.prototype.slice.call(self.listElements).forEach(function (x) {
                    x.classList.remove("hidden-search");
                });
            } 
            self.drop.style.visibility = "hidden";
        }
    }
    this.init();
    this.checkUncheckAll();
}

vanillaSelectBox.prototype.buildSelect = function (data) {
    let self = this;
    if(data == null || data.length < 1) return;
    if(!self.isOptgroups){
        self.isOptgroups = data[0].parent != undefined && data[0].parent != "";
    }
  
    if(self.isOptgroups){
        let groups = {};
        data = data.filter(function(x){
            return x.parent != undefined && x.parent != "";
        });
    
        data.forEach(function (x) {
            if(!groups[x.parent]){
                groups[x.parent] = true;
            }
        });
        for (let group in groups) {
            let anOptgroup = document.createElement("optgroup");
            anOptgroup.setAttribute("label", group);
            
            options = data.filter(function(x){
                return x.parent == group;
            });
            options.forEach(function (x) {
                let anOption = document.createElement("option");
                anOption.value = x.value;
                anOption.text = x.text;
                if(x.selected){
                    anOption.setAttribute("selected",true)
                }
                anOptgroup.appendChild(anOption);
            });
            self.root.appendChild(anOptgroup);
        }
    }else{
        data.forEach(function (x) {
            let anOption = document.createElement("option");
            anOption.value = x.value;
            anOption.text = x.text;
            if(x.selected){
                anOption.setAttribute("selected",true)
            }
            self.root.appendChild(anOption);
        });
    }
}

vanillaSelectBox.prototype.remoteSearchIntegrate = function (data) {
    let self = this;

    if (data == null || data.length == 0) {
        let dataChecked = self.optionsCheckedToData();
        if(dataChecked)
            data = dataChecked.slice(0);
        self.remoteSearchIntegrateIt(data);
    } else {
        let dataChecked = self.optionsCheckedToData();
        /*
        if (dataChecked.length > 0){
            for (var i = data.length - 1; i >= 0; i--) {
                if(dataChecked.indexOf(data[i].id) !=-1){
                    data.slice(i,1);
                }
            }
        }*/
        let dc_value = Array()
        for (dc of dataChecked){
            dc_value = dc_value.concat(dc['value'])
        }
        let final_data = Array()
        for (dd of data){
            if (!dc_value.includes(dd['value'])){
                final_data = final_data.concat(dd)
            }
        }
        
        //data = final_data.concat(dataChecked);
        data = dataChecked.concat(final_data);
        self.remoteSearchIntegrateIt(data);
    }
}

vanillaSelectBox.prototype.optionsCheckedToData = function () {
    let self = this;
    let dataChecked = [];
    let treeOptions = self.ul.querySelectorAll("li.active:not(.grouped-option)");
    let keepParents = {};
        if (treeOptions) {
            Array.prototype.slice.call(treeOptions).forEach(function (x) {
                let oneData = {"value":x.getAttribute("data-value"),"text":x.getAttribute("data-text"),"selected":true};
                if(oneData.value !== "all"){
                    if(self.isOptgroups){
                        let parentId = x.getAttribute("data-parent");
                        if(keepParents[parentId]!=undefined){
                            oneData.parent = keepParents[parentId];
                        }else{
                            let parentPtr = self.ul.querySelector("#"+parentId);
                            let parentName = parentPtr.getAttribute("data-text");
                            keepParents[parentId] = parentName;
                            oneData.parent = parentName;
                        }
                    }
                    dataChecked.push(oneData);
                }
            });
        }
        return dataChecked;
}

vanillaSelectBox.prototype.removeOptionsNotChecked = function (data) {
    let self = this;
    let minimumSize = self.onInitSize;
    let newSearchSize = data == null ? 0 : data.length;
    let presentSize = self.root.length;
    if (presentSize + newSearchSize > minimumSize) {
        let maxToRemove = presentSize + newSearchSize - minimumSize - 1;
        let removed = 0;
        for (var i = self.root.length - 1; i >= 0; i--) {
            if (self.root.options[i].selected == false) {
                if (removed <= maxToRemove) {
                    removed++;
                    self.root.remove(i);
                }
            }
        }
    }
}

vanillaSelectBox.prototype.changeTree = function (data, options) {
    let self = this;
    self.empty();
    self.remoteSearchIntegrateIt(data);
    if (options && options.onSearch) {
        if (typeof options.onSearch === 'function') {
            self.onSearch = options.onSearch;
            self.isSearchRemote = true;
        }
    }
    self.listElements = this.drop.querySelectorAll("li:not(.grouped-option)");
}

vanillaSelectBox.prototype.remoteSearchIntegrateIt = function (data) {
    let self = this;
    if (data == null || data.length == 0) return;
    while(self.root.firstChild)
    self.root.removeChild(self.root.firstChild);
    
    self.buildSelect(data);
    self.reloadTree();
}

vanillaSelectBox.prototype.reloadTree = function () {
    let self = this;
    let lis = self.ul.querySelectorAll("li");
    if (lis != null) {
        for (var i = lis.length - 1; i >= 0; i--) {
            if (lis[i].getAttribute('data-value') !== 'all') {
                self.ul.removeChild(lis[i]);
            }
        }
    }

    let selectedTexts = ""
    let sep = "";
    let nrActives = 0;
    let nrAll = 0;

    if (self.isOptgroups) {
        if (document.querySelector(self.domSelector + ' optgroup') !== null) {
            self.options = document.querySelectorAll(this.domSelector + " option");
            let groups = document.querySelectorAll(this.domSelector + ' optgroup');
            Array.prototype.slice.call(groups).forEach(function (group) {
                let groupOptions = group.querySelectorAll('option');
                let li = document.createElement("li");
                let span = document.createElement("span");
                let iCheck = document.createElement("i");
                let labelElement = document.createElement("b");
                let dataWay = group.getAttribute("data-way");
                if (!dataWay) dataWay = "closed";
                if (!dataWay || (dataWay !== "closed" && dataWay !== "open")) dataWay = "closed";
                li.appendChild(span);
                li.appendChild(iCheck);
                self.ul.appendChild(li);
                li.classList.add('grouped-option');
                li.classList.add(dataWay);
                self.currentOptgroup++;
                let optId = self.rootToken + "-opt-" + self.currentOptgroup;
                li.id = optId;
                li.appendChild(labelElement);
                labelElement.appendChild(document.createTextNode(group.label));
                li.setAttribute("data-text", group.label);
                self.ul.appendChild(li);

                Array.prototype.slice.call(groupOptions).forEach(function (x) {
                    let text = x.textContent;
                    let value = x.value;
                    let classes = x.getAttribute("class");
                    if (classes) {
                        classes = classes.split(" ");
                    }
                    else {
                        classes = [];
                    }
                    classes.push(dataWay);
                    let li = document.createElement("li");
                    let isSelected = x.hasAttribute("selected");
                    self.ul.appendChild(li);
                    li.setAttribute("data-value", value);
                    li.setAttribute("data-text", text);
                    li.setAttribute("data-parent", optId);
                    if (classes.length != 0) {
                        classes.forEach(function (x) {
                            li.classList.add(x);
                        });
                    }
                    if (isSelected) {
                        nrActives++;
                        selectedTexts += sep + text;
                        sep = self.userOptions.buttonItemsSeparator;
                        li.classList.add("active");
                        if (!self.isMultiple) {
                            self.title.textContent = text;
                            if (classes.length != 0) {
                                classes.forEach(function (x) {
                                    self.title.classList.add(x);
                                });
                            }
                        }
                    }
                    li.appendChild(document.createTextNode(text));
                })
            })
        }
        self.listElements = this.drop.querySelectorAll("li:not(.grouped-option)");
    } else {
        self.options = self.root.querySelectorAll("option");
        Array.prototype.slice.call(self.options).forEach(function (x) {
            let text = x.textContent;
            let value = x.value;
            if (value != "all") {
                let originalAttrs;
                if (x.hasAttributes()) {
                    originalAttrs = Array.prototype.slice.call(x.attributes)
                        .filter(function (a) {
                            return self.forbidenAttributes.indexOf(a.name) === -1
                        });
                }
                let classes = x.getAttribute("class");
                if (classes) {
                    classes = classes
                        .split(" ")
                        .filter(function (c) {
                            return self.forbidenClasses.indexOf(c) === -1
                        });
                } else {
                    classes = [];
                }
                let li = document.createElement("li");
                let isSelected = x.hasAttribute("selected");

                let isDisabled = x.disabled;

                self.ul.appendChild(li);
                li.setAttribute("data-value", value);
                li.setAttribute("data-text", text);

                if (originalAttrs !== undefined) {
                    originalAttrs.forEach(function (a) {
                        li.setAttribute(a.name, a.value);
                    });
                }

                classes.forEach(function (x) {
                    li.classList.add(x);
                });

                if (self.maxOptionWidth < Infinity) {
                    li.classList.add("short");
                    li.style.maxWidth = self.maxOptionWidth + "px";
                }

                if (isSelected) {
                    nrActives++;
                    selectedTexts += sep + text;
                    sep = self.userOptions.buttonItemsSeparator;
                    li.classList.add("active");
                    if (!self.isMultiple) {
                        self.title.textContent = text;
                        if (classes.length != 0) {
                            classes.forEach(function (x) {
                                self.title.classList.add(x);
                            });
                        }
                    }
                }
                if (isDisabled) {
                    li.classList.add("disabled");
                }
                li.appendChild(document.createTextNode(" " + text));
            }
        });
    }

}

vanillaSelectBox.prototype.disableItems = function (values) {
    let self = this;
    let foundValues = [];
    if (vanillaSelectBox_type(values) == "string") {
        values = values.split(",");
    }

    if (vanillaSelectBox_type(values) == "array") {
        Array.prototype.slice.call(self.options).forEach(function (x) {
            if (values.indexOf(x.value) != -1) {
                foundValues.push(x.value);
                x.setAttribute("disabled", "");
            }
        });
    }
    Array.prototype.slice.call(self.listElements).forEach(function (x) {
        let val = x.getAttribute("data-value");
        if (foundValues.indexOf(val) != -1) {
            x.classList.add("disabled");
        }
    });
}

vanillaSelectBox.prototype.enableItems = function (values) {
    let self = this;
    let foundValues = [];
    if (vanillaSelectBox_type(values) == "string") {
        values = values.split(",");
    }

    if (vanillaSelectBox_type(values) == "array") {
        Array.prototype.slice.call(self.options).forEach(function (x) {
            if (values.indexOf(x.value) != -1) {
                foundValues.push(x.value);
                x.removeAttribute("disabled");
            }
        });
    }

    Array.prototype.slice.call(self.listElements).forEach(function (x) {
        if (foundValues.indexOf(x.getAttribute("data-value")) != -1) {
            x.classList.remove("disabled");
        }
    });
}

vanillaSelectBox.prototype.checkSelectMax = function (nrActives) {
    let self = this;
    if (self.maxSelect == Infinity || !self.isMultiple) return;
    if (self.maxSelect <= nrActives) {
        Array.prototype.slice.call(self.listElements).forEach(function (x) {
            if (x.hasAttribute('data-value')) {
                if (!x.classList.contains('disabled') && !x.classList.contains('active')) {
                    x.classList.add("overflow");
                }
            }
        });
    } else {
        Array.prototype.slice.call(self.listElements).forEach(function (x) {
            if (x.classList.contains('overflow')) {
                x.classList.remove("overflow");
            }
        });
    }
}

vanillaSelectBox.prototype.checkUncheckFromChild = function (liClicked) {
    let self = this;
    let parentId = liClicked.getAttribute('data-parent');
    let parentLi = document.getElementById(parentId);
    if (!self.isMultiple) return;
    let listElements = self.drop.querySelectorAll("li");
    let childrenElements = Array.prototype.slice.call(listElements).filter(function (el) {
        return el.hasAttribute("data-parent") && el.getAttribute('data-parent') == parentId  && !el.classList.contains('hidden-search') ;
    });
    let nrChecked = 0;
    let nrCheckable = childrenElements.length;
    if (nrCheckable == 0) return;
    childrenElements.forEach(function (el) {
        if (el.classList.contains('active')) nrChecked++;
    });
    if (nrChecked === nrCheckable || nrChecked === 0) {
        if (nrChecked === 0) {
            parentLi.classList.remove("checked");
        } else {
            parentLi.classList.add("checked");
        }
    } else {
        parentLi.classList.remove("checked");
    }
}

vanillaSelectBox.prototype.checkUncheckFromParent = function (liClicked) {
    let self = this;
    let parentId = liClicked.id;
    if (!self.isMultiple) return;
    let listElements = self.drop.querySelectorAll("li");
    let childrenElements = Array.prototype.slice.call(listElements).filter(function (el) {
        return el.hasAttribute("data-parent") && el.getAttribute('data-parent') == parentId && !el.classList.contains('hidden-search');
    });
    let nrChecked = 0;
    let nrCheckable = childrenElements.length;
    if (nrCheckable == 0) return;
    childrenElements.forEach(function (el) {
        if (el.classList.contains('active')) nrChecked++;
    });
    if (nrChecked === nrCheckable || nrChecked === 0) {
        //check all or uncheckAll : just do the opposite
        childrenElements.forEach(function (el) {
            var event = document.createEvent('HTMLEvents');
            event.initEvent('click', true, false);
            el.dispatchEvent(event);
        });
        if (nrChecked === 0) {
            liClicked.classList.add("checked");
        } else {
            liClicked.classList.remove("checked");
        }
    } else {
        //check all
        liClicked.classList.remove("checked");
        childrenElements.forEach(function (el) {
            if (!el.classList.contains('active')) {
                var event = document.createEvent('HTMLEvents');
                event.initEvent('click', true, false);
                el.dispatchEvent(event);
            }
        });
    }
}

vanillaSelectBox.prototype.checkUncheckAll = function () {
    let self = this;
    if (!self.isMultiple) return;
    let nrChecked = 0;
    let nrCheckable = 0;
    let totalAvailableElements = 0;
    let checkAllElement = null;
    if (self.listElements == null) return;
    Array.prototype.slice.call(self.listElements).forEach(function (x) {
        if (x.hasAttribute('data-value')) {
            if (x.getAttribute('data-value') === 'all') {
                checkAllElement = x;
            }
            if (x.getAttribute('data-value') !== 'all'
                && !x.classList.contains('hidden-search')
                && !x.classList.contains('disabled')) {
                nrCheckable++;
                nrChecked += x.classList.contains('active');
            }
            if (x.getAttribute('data-value') !== 'all'
                && !x.classList.contains('disabled')) {
                totalAvailableElements++;
            }
        }
    });

    if (checkAllElement) {
        if (nrChecked === nrCheckable) {
            // check the checkAll checkbox
            /*
            if (nrChecked === totalAvailableElements) {
                self.title.textContent = self.userOptions.translations.all;
            }*/
            checkAllElement.classList.add("active");
            checkAllElement.innerText = self.userOptions.translations.clearAll;
            checkAllElement.setAttribute('data-selected', 'true')
        } else if (nrChecked === 0) {
            // uncheck the checkAll checkbox
            self.title.textContent = self.userOptions.placeHolder;
            checkAllElement.classList.remove("active");
            checkAllElement.innerText = self.userOptions.translations.selectAll;
            checkAllElement.setAttribute('data-selected', 'false')
        }
    }
}

vanillaSelectBox.prototype.setValue = function (values) {
    let self = this;
    let listElements = self.drop.querySelectorAll("li");

    if (values == null || values == undefined || values == "") {
        self.empty();
    } else {
        if (self.isMultiple) {
            if (vanillaSelectBox_type(values) == "string") {
                if (values === "all") {
                    values = [];
                    Array.prototype.slice.call(listElements).forEach(function (x) {
                        if (x.hasAttribute('data-value')) {
                            let value = x.getAttribute('data-value');
                            if (value !== 'all') {
                                if (!x.classList.contains('hidden-search') && !x.classList.contains('disabled')) {
                                    values.push(x.getAttribute('data-value'));
                                }
                                // already checked (but hidden by search)
                                if (x.classList.contains('active')) {
                                    if (x.classList.contains('hidden-search') || x.classList.contains('disabled')) {
                                        values.push(value);
                                    }
                                }
                            }else{
                                x.classList.add("active");
                            }
                        } else if (x.classList.contains('grouped-option')) {
                            x.classList.add("checked");
                        }
                    });
                } else if (values === "none") {
                    values = [];
                    Array.prototype.slice.call(listElements).forEach(function (x) {
                        if (x.hasAttribute('data-value')) {
                            let value = x.getAttribute('data-value');
                            if (value !== 'all') {
                                if (x.classList.contains('active')) {
                                    if (x.classList.contains('hidden-search') || x.classList.contains('disabled')) {
                                        values.push(value);
                                    }
                                }
                            }
                        } else if (x.classList.contains('grouped-option')) {
                            x.classList.remove("checked");
                        }
                    });
                } else {
                    values = values.split(",");
                }
            }
            let foundValues = [];
            if (vanillaSelectBox_type(values) == "array") {
                Array.prototype.slice.call(self.options).forEach(function (x) {
                    if (values.indexOf(x.value) !== -1) {
                        x.selected = true;
                        foundValues.push(x.value);
                    } else {
                        x.selected = false;
                    }
                });
                let selectedTexts = ""
                let sep = "";
                let nrActives = 0;
                let nrAll = 0;
                Array.prototype.slice.call(listElements).forEach(function (x) {
                    if (x.value !== 'all') {
                        nrAll++;
                    }                    
                    if (foundValues.indexOf(x.getAttribute("data-value")) != -1) {
                        x.classList.add("active");
                        nrActives++;
                        selectedTexts += sep + x.getAttribute("data-text");
                        sep = self.userOptions.buttonItemsSeparator;
                    } else {
                        x.classList.remove("active");
                    }
                });
                /*
                if (nrAll == nrActives - Number(!self.userOptions.disableSelectAll)) {
                    let wordForAll = self.userOptions.translations.all;
                    selectedTexts = wordForAll;
                } else */
                
                if (self.multipleSize != -1) {
                    if (nrActives > self.multipleSize) {
                        let wordForItems = nrActives === 1 ? self.userOptions.translations.item : self.userOptions.translations.items;
                        selectedTexts = nrActives + " " + wordForItems;
                    }
                }
                self.title.textContent = selectedTexts;
                self.privateSendChange();
            }
            self.checkUncheckAll();
        } else {
            let found = false;
            let text = "";
            let classNames = ""
            Array.prototype.slice.call(listElements).forEach(function (x) {
                let liVal = x.getAttribute("data-value");
                if (liVal == values) {
                    x.classList.add("active");
                    found = true;
                    text = x.getAttribute("data-text")
                } else {
                    x.classList.remove("active");
                }
            });
            Array.prototype.slice.call(self.options).forEach(function (x) {
                if (x.value == values) {
                    x.selected = true;
                    className = x.getAttribute("class");
                    if (!className) className = "";
                } else {
                    x.selected = false;
                }
            });
            if (found) {
                self.title.textContent = text;
                if (self.userOptions.placeHolder != "" && self.title.textContent == "") {
                    self.title.textContent = self.userOptions.placeHolder;
                }
                if (className != "") {
                    self.title.setAttribute("class", className + " title");
                } else {
                    self.title.setAttribute("class", "title");
                }
            }
        }
    }
}

vanillaSelectBox.prototype.privateSendChange = function () {
    let event = document.createEvent('HTMLEvents');
    event.initEvent('change', true, false);
    this.root.dispatchEvent(event);
}

vanillaSelectBox.prototype.empty = function () {
    Array.prototype.slice.call(this.listElements).forEach(function (x) {
        x.classList.remove("active");
    });
    let parentElements = this.drop.querySelectorAll("li.grouped-option");
    if(parentElements){
        Array.prototype.slice.call(parentElements).forEach(function (x) {
            x.classList.remove("checked");
        });
    }
    Array.prototype.slice.call(this.options).forEach(function (x) {
        x.selected = false;
    });
    this.title.textContent = "";
    if (this.userOptions.placeHolder != "" && this.title.textContent == "") {
        this.title.textContent = this.userOptions.placeHolder;
    }
    this.checkUncheckAll();
    this.privateSendChange();
}

vanillaSelectBox.prototype.destroy = function () {
    let already = document.getElementById("btn-group-" + this.rootToken);
    if (already) {
        VSBoxCounter.remove(this.instanceOffset);
        already.remove();
        this.root.style.display = "inline-block";
    }
}
vanillaSelectBox.prototype.disable = function () {
    this.main.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
    });
    let already = document.getElementById("btn-group-" + this.rootToken);
    if (already) {
        button = already.querySelector("button")
        if (button) button.classList.add("disabled");
        this.isDisabled = true;
    }
}
vanillaSelectBox.prototype.enable = function () {
    let already = document.getElementById("btn-group-" + this.rootToken);
    if (already) {
        button = already.querySelector("button")
        if (button) button.classList.remove("disabled");
        this.isDisabled = false;
    }
}

vanillaSelectBox.prototype.showOptions = function () {
    console.log(this.userOptions);
}
// Polyfills for IE
if (!('remove' in Element.prototype)) {
    Element.prototype.remove = function () {
        if (this.parentNode) {
            this.parentNode.removeChild(this);
        }
    };
}

function vanillaSelectBox_type(target) {
    const computedType = Object.prototype.toString.call(target);
    const stripped = computedType.replace("[object ", "").replace("]", "");
    const lowercased = stripped.toLowerCase();
    return lowercased;
}
