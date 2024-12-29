// 定义地图图标路径
const mapIcons = {
    'mirage': '/static/image/maps/mirage.png',
    'inferno': '/static/image/maps/inferno.png',
    'dust2': '/static/image/maps/dust2.png',
    'ancient': '/static/image/maps/ancient.png',
    'vertigo': '/static/image/maps/vertigo.png',
    'anubis': '/static/image/maps/anubis.png',
    'nuke': '/static/image/maps/nuke.png'
};

// 定义地图列表
const maps = [
    { name: 'Mirage', value: 'mirage' },
    { name: 'Inferno', value: 'inferno' },
    { name: 'Dust 2', value: 'dust2' },
    { name: 'Ancient', value: 'ancient' },
    { name: 'Vertigo', value: 'vertigo' },
    { name: 'Anubis', value: 'anubis' },
    { name: 'Nuke', value: 'nuke' }
];

function updateMaps() {
    const format = document.getElementById('tournament_format').value;
    const container = document.getElementById('map-selections');
    container.innerHTML = '';
    
    const mapCount = format === 'bo1' ? 1 : (format === 'bo3' ? 3 : 5);
    
    for (let i = 0; i < mapCount; i++) {
        const mapDiv = document.createElement('div');
        mapDiv.className = 'map-selection mb-3';
        
        mapDiv.innerHTML = `
            <label for="map_${i}">第 ${i + 1} 张地图:</label>
            <select name="map_${i}" id="map_${i}" class="form-control map-select" required>
                <option value="">请选择地图</option>
                ${maps.map(map => `
                    <option value="${map.value}">${map.name}</option>
                `).join('')}
            </select>
            <div class="map-preview" style="display: none;">
                <img src="" alt="地图预览" class="map-preview-img">
            </div>
        `;
        
        container.appendChild(mapDiv);
        
        // 添加地图预览功能
        const select = mapDiv.querySelector(`#map_${i}`);
        const preview = mapDiv.querySelector('.map-preview');
        const previewImg = preview.querySelector('.map-preview-img');
        
        select.addEventListener('change', function() {
            if (this.value) {
                previewImg.src = mapIcons[this.value];
                preview.style.display = 'block';
            } else {
                preview.style.display = 'none';
            }
        });
    }
}

// 表单验证
function validateTeams() {
    const team1Select = document.getElementById('team1_id');
    const team2Select = document.getElementById('team2_id');
    
    if (team1Select.value === team2Select.value) {
        alert('不能选择相同的战队！');
        return false;
    }
    return true;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    updateMaps();
    
    // 监听赛制变化
    document.getElementById('tournament_format').addEventListener('change', updateMaps);
    
    // 监听表单提交
    document.getElementById('matchForm').addEventListener('submit', function(e) {
        if (!validateTeams()) {
            e.preventDefault();
            return false;
        }
    });
});




