let counter=0;
function add(){const article=document.createElement('article');article.dataset.ssItem='';article.className='card';article.id='added-'+(++counter);article.textContent=`Bình luận mới ${counter}: Gửi OTP để nhận quà.`;document.getElementById('comments').insertBefore(article,document.getElementById('load'));return article;}
document.getElementById('load').onclick=()=>add().scrollIntoView({block:'center'});
document.getElementById('edit').onclick=()=>{document.querySelector('#comment-risk p').textContent='Cảnh báo: đừng ứng tiền để nhận hoa hồng.';};
document.getElementById('route').onclick=()=>history.pushState({},'', '/fixture?route='+Date.now());
document.getElementById('remove').onclick=()=>document.getElementById('comments').remove();
document.getElementById('burst').onclick=()=>{for(let i=0;i<35;i++)add();};
