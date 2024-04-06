const preventDefaultKeys = [
  'SoftLeft',
  'Call',
  'Enter',
  'MicrophoneToggle',
  'EndCall',
  'AudioVolumeDown',
  'AudioVolumeUp',
  'ArrowUp',
  'ArrowDown'
];
const preventDefaultIfEmptyKeys = [
  'Backspace'
];
const blurKeys = [
  'EndCall'
];
const blurIfEmptyKeys = [
  'Backspace'
];
function logOut(event) {
  localStorage.removeItem("ellisbakeshop-csrf-token");
  window.location.replace("signup.html");
}
function defaultHandler(event) {
  if (!event || !event.target) {
    return undefined;
  }
  let xmlHttp = event.target;
  if (xmlHttp.status == 403) {
    logOut(event);
  }
  let result = {};
  try {
    result = JSON.parse(xmlHttp.responseText);
  } catch(e) {
    try {
      result = {'message': xmlHttp.responseText};
    } catch (e2) {
      result = undefined;
    }
  }
  return {statusCode: xmlHttp.status, responseJson: result};
}
function getParameterByName(name, url = window.location.href) {
  name = name.replace(new RegExp("[[]]", "g"), "\\$&");
  let regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)");
  let results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return "";
  return decodeURIComponent(results[2].replace(/\+/g, " "));
}
function iosCookieRefresh(event) {
  let cookieRefreshTime = localStorage.getItem(
    "ellisbakeshop-cookie-refresh-time"
  );
  if (
    !cookieRefreshTime ||
    !new RegExp("d+").test(cookieRefreshTime) ||
    parseInt(cookieRefreshTime) < new Date().getTime()
  ) {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", API_DOMAIN + "/ios-cookie-refresh", true);
    xmlHttp.withCredentials = true;
    xmlHttp.onload = handleIosCookieRefresh;
    xmlHttp.send(
      JSON.stringify({
        csrf: csrfToken
      })
    );
  }
}
function handleIosCookieRefresh(event) {
  let xmlHttp = event.target;
  let timeInt = new Date().getTime() + 86400000;
  localStorage.setItem("ellisbakeshop-cookie-refresh-time", timeInt.toString());
}
function findParentWithClass(element, className) {
  let current = element;
  while (!!current) {
    if (current.classList.contains(className)) {
      return current;
    }
    current = current.parentElement;
  }
  return current;
}
// https://stackoverflow.com/a/7616484/9313980
function hashCode(input) {
  var hash = 0, i, chr;
  if (input.length === 0) return hash.toString();
  for (i = 0; i < input.length; i++) {
      chr = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + chr;
      hash |= 0; // Convert to 32bit integer
  }
  return hash.toString();
}
const dateRegex = /^(\d{4})-(\d{2})-(\d{2})$/;
function getTodayOrUrlParam() {
  let year = 0;
  let month = 0;
  let day = 0;

  let youStillNeedToFigureOutTodaysDate = true;

  // first check if you have a URL param
  let urlParam = getParameterByName("date");
  if (urlParam) {
    // if so, check if its valid
    if (dateRegex.test(urlParam)) {
      let regexResult = dateRegex.exec(urlParam);
      year = regexResult[1];
      month = regexResult[2];
      day = regexResult[3];
      youStillNeedToFigureOutTodaysDate = false;
    }
  }
  if (youStillNeedToFigureOutTodaysDate) {
    let d = new Date();
    year = (d.getFullYear()).toString();
    month = (d.getMonth() + 1).toString();
    day = (d.getDate()).toString();
    
    if (month.length < 2) {
      month = '0' + month;
    }
    if (day.length < 2) {
      day = '0' + day;
    }
  }

  return `${year}-${month}-${day}`;
}
function closeModalIfApplicable(event) {
  if (event.target.classList.contains("modal-bg")) {
    event.target.getElementsByClassName("modal")[0].style.display = "none";
    event.target.style.display = "none";
  }
}
function closeModal(event) {
  let parent = findParentWithClass(event.target, "modal-bg");
  if (parent) {
    parent.style.display = "none";
  }
}
function arrowKeyEmulator(event, functionHandle) {
  if (preventDefaultKeys.includes(event.key) || (preventDefaultIfEmptyKeys.includes(event.key) && !event.target.value)) {
    event.preventDefault();
  }
  if (blurKeys.includes(event.key)) {
    event.target.blur();
  }
  if (event.type === 'keyup' && blurIfEmptyKeys.includes(event.key) && !event.target.value && !previousValue) {
    event.target.blur();
  }
  if (event.type === 'keydown' && ['ArrowUp', 'ArrowDown'].includes(event.key)) {
    let inputs = Array.from(document.getElementsByClassName('navigable-input'));
    if (event.target.hasAttribute('input-group-name')) {
      const currentTarget = event.target.getAttribute('input-group-name');
      inputs = inputs.filter(x=>x.getAttribute('input-group-name') == currentTarget);
    }
    let index = inputs.indexOf(event.target);
    index = index + (event.key === 'ArrowUp' ? -1 : 1);
    index = index < 0 ? inputs.length - 1 : index;
    index = index > inputs.length - 1 ? 0 : index;
    inputs[index].focus();
    if (event.type === 'keydown' && 
        (inputs[index].hasAttribute('linked-item'))) {
      let checkbox = inputs[index].parentElement.getElementsByClassName('selectable')[0];
      checkbox.classList.add('selected');
    }
  }
  if (event.type === 'keydown' && (event.target.hasAttribute('linked-item')) && ['Enter'].includes(event.key)) {
    let button = event.target.parentElement.getElementsByClassName('selectable')[0];
    button.click();
  }
  if (functionHandle) {
    functionHandle(event);
  }
}
function blurEmulator(event) {
  let selecteds = Array.from(document.getElementsByClassName('selected'));
  selecteds.forEach(x=>x.classList.remove('selected'));
}
function applyEmulators() {
  let allItems = Array.from(document.querySelectorAll(`[input-group-name]`));
  for (let i = 0; i < allItems.length; i++) {
    let item = allItems[i];
    if (item.hasAttribute('generated')) {
      continue;
    }
    if (item.tagName.toLowerCase() == 'input' && ['tel','number','text'].includes(item.type.toLowerCase())) {
      item.addEventListener('keydown', arrowKeyEmulator);
      item.addEventListener('keyup', arrowKeyEmulator);
      item.setAttribute('generated', true);
      item.classList.add('navigable-input');
    } else if (item.tagName.toLowerCase() == 'a' || item.tagName.toLowerCase() == 'button' || (item.tagName.toLowerCase() == 'input' && ['checkbox'].includes(item.type.toLowerCase()))) {
      let invisibleInput = document.createElement('input');
      invisibleInput.type = 'text';
      invisibleInput.classList.add('invisible-input');
      invisibleInput.classList.add('navigable-input');
      invisibleInput.setAttribute('input-group-name', item.getAttribute('input-group-name'));
      invisibleInput.setAttribute('generated', true);
      invisibleInput.setAttribute('linked-item', true);
      invisibleInput.addEventListener('keydown', arrowKeyEmulator);
      invisibleInput.addEventListener('keyup', arrowKeyEmulator);
      invisibleInput.addEventListener('blur', blurEmulator);
      invisibleInput.tabIndex = '-1';

      item.parentElement.appendChild(invisibleInput);
      item.removeAttribute('input-group-name');
      item.classList.add('selectable');
    }
  }
}
applyEmulators();
// allows for clicking the background of the modal to exit the modal
let modalBackgrounds = document.getElementsByClassName("modal-bg");
for (let i = 0; i < modalBackgrounds.length; i++) {
  modalBg = modalBackgrounds[i];
  modalBg.style.display = "none";
  modalBg.addEventListener("click", closeModalIfApplicable);
}
const csrfToken = localStorage.getItem("ellisbakeshop-csrf-token");
// warn users who open the console to not do anything dumb
console.log('%cStop!', 'color: red; font-size: 100px; font-weight: bold; -webkit-text-stroke: 2px black;');
console.log('If someone told you to paste something in here, %cDO NOT DO IT!', 'color: red; font-size: 20px; font-weight: bold; -webkit-text-stroke: 1px black;', 'They are trying to hijack your account!');
// if you are deploying this on a different domain, you'll
// need to change these values here
const API_DOMAIN = "https://api.ellisbakeshop.com";
const UI_DOMAIN = "https://www.ellisbakeshop.com";
