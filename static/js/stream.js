var popupBlocked = false;

window.open = function () {
  if (!popupBlocked) {
    console.log('Popup blocked by protection script');
    popupBlocked = true;
  }
  return null;
};

function unlockStream() {
  document.getElementById('overlay').classList.add('hidden');
  document.getElementById('full-screen-iframe').classList.add('unlocked');

  // Temporarily engage a click absorber to catch the first popup-triggering click
  const absorber = document.getElementById('click-absorber');
  absorber.style.display = 'block';

  // After 1 second, remove the click absorber, allowing normal interaction.
  setTimeout(() => {
    absorber.style.display = 'none';
  }, 1000);
}

document.addEventListener(
  'click',
  function (e) {
    if (e.target.tagName === 'A' && e.target.target === '_blank') {
      if (!e.target.href.includes('lotusgamehd.xyz')) {
        e.preventDefault();
        console.log('External link blocked:', e.target.href);
        return false;
      }
    }
  },
  true,
);
