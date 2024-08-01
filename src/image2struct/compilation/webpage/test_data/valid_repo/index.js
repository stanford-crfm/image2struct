const phrases = [
  'Ты уверена?',
  'Точно уверена?',
  'Подумай еще раз',
  'Последний шанс!',
  'Неужели нет?',
  'Ты можешь пожалеть об этом',
  'Не торопись, подумай еще',
  'Ты абсолютно в этом уверена?',
  'Это может стать ошибкой',
  'Может ты передумаешь?',
  'Не будь такой холодной',
  'Это твой конечный ответ?',
  'Ты разобьешь мне сердце :(',
];

const btns = document.querySelector('.buttons');
const yes = document.querySelector('.yes');
const no = document.querySelector('.no');
const img = document.querySelector('img');
const text = document.querySelector('.text');

yes.addEventListener('click', (event) => {
  if (event.target) {
    btns.style.display = 'none';
    img.src = './images/giphy_2.gif';
    img.style.cssText += `width: 500px`;
    text.innerText = 'Урааа, спасибо!';

    if (window.innerWidth > 768) {
      img.style.cssText += `width: 500px`;
    } else {
      img.style.cssText += `
        width: 250px;
        margin-top: 200px;
      `;
    }
  }
});

let i = 0;
let scale1 = 1;
let scale2 = 1;
let margin = 0;

no.addEventListener('click', (event) => {
  if (event.target) {
    no.innerText = phrases[i];
    i++;

    scale1 -= 0.05;
    scale2 += 0.05;
    margin += 5;

    no.style.transform = `scale(${scale1})`;
    yes.style.cssText += `
        transform: scale(${scale2});
        margin-left: ${margin}px;
    `;

    if (i === phrases.length) i = 0;
  }
});
