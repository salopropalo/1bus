// Сохранение последних выбранных значений для полей формы
const STORAGE_KEYS = {
    rated_current: 'last_rated_current',
    conductors: 'last_conductors',
    material: 'last_material',
    line: 'last_line',
    nomenclature: 'last_nomenclature'
};

// Загрузка сохранённых значений при открытии модалки
function loadLastValues() {
    const ratedCurrentSelect = document.getElementById('rated_current');
    const conductorsSelect = document.getElementById('conductors');
    const materialSelect = document.getElementById('material');
    const lineSelect = document.getElementById('lineSelect');
    const lineNewInput = document.getElementById('lineNewInput');
    const nomenclatureSelect = document.getElementById('nomenclature');

    const lastRated = sessionStorage.getItem(STORAGE_KEYS.rated_current);
    const lastConductors = sessionStorage.getItem(STORAGE_KEYS.conductors);
    const lastMaterial = sessionStorage.getItem(STORAGE_KEYS.material);
    const lastLine = sessionStorage.getItem(STORAGE_KEYS.line);
    const lastNomenclature = sessionStorage.getItem(STORAGE_KEYS.nomenclature);

    // Восстанавливаем простые селекты
    if (lastRated && ratedCurrentSelect) ratedCurrentSelect.value = lastRated;
    if (lastConductors && conductorsSelect) conductorsSelect.value = lastConductors;
    if (lastMaterial && materialSelect) materialSelect.value = lastMaterial;

    // Восстанавливаем номенклатуру с проверкой существования опции
    if (lastNomenclature && nomenclatureSelect) {
        const optionExists = [...nomenclatureSelect.options].some(opt => opt.value === lastNomenclature);
        if (optionExists) {
            nomenclatureSelect.value = lastNomenclature;
        }
    }

    // Восстанавливаем линию: сначала пробуем найти в select
    if (lastLine && lineSelect) {
        const option = [...lineSelect.options].find(o => o.value === lastLine);
        if (option) {
            // Линия есть в списке — выбираем её
            lineSelect.value = lastLine;
            lineSelect.setAttribute('name', 'line');
            lineNewInput.style.display = 'none';
            lineNewInput.removeAttribute('name');
        } else {
            // Линия была новой — показываем поле ввода
            lineSelect.value = '__new__';
            lineSelect.removeAttribute('name');
            lineNewInput.style.display = 'block';
            lineNewInput.setAttribute('name', 'line');
            lineNewInput.value = lastLine;
            lineNewInput.required = true;
        }
    }
}

// Сохранение текущих значений всех полей в sessionStorage
function saveCurrentValues() {
    const ratedCurrentSelect = document.getElementById('rated_current');
    const conductorsSelect = document.getElementById('conductors');
    const materialSelect = document.getElementById('material');
    const lineSelect = document.getElementById('lineSelect');
    const lineNewInput = document.getElementById('lineNewInput');
    const nomenclatureSelect = document.getElementById('nomenclature');

    if (ratedCurrentSelect.value) {
        sessionStorage.setItem(STORAGE_KEYS.rated_current, ratedCurrentSelect.value);
    }
    if (conductorsSelect.value) {
        sessionStorage.setItem(STORAGE_KEYS.conductors, conductorsSelect.value);
    }
    if (materialSelect.value) {
        sessionStorage.setItem(STORAGE_KEYS.material, materialSelect.value);
    }
    if (nomenclatureSelect.value) {
        sessionStorage.setItem(STORAGE_KEYS.nomenclature, nomenclatureSelect.value);
    }

    // Сохраняем линию: новую из input или выбранную из select
    if (lineSelect.value === '__new__' && lineNewInput.value.trim()) {
        sessionStorage.setItem(STORAGE_KEYS.line, lineNewInput.value.trim());
    } else if (lineSelect.value && lineSelect.value !== '__new__') {
        sessionStorage.setItem(STORAGE_KEYS.line, lineSelect.value);
    }
}

// Восстанавливаем значения при загрузке страницы
document.addEventListener('DOMContentLoaded', loadLastValues);

// Перед отправкой формы сохраняем выбранные параметры
const form = document.getElementById('addSpecificationForm');
if (form) {
    form.addEventListener('submit', function() {
        saveCurrentValues();
    });
}

// Обработчик переключения между существующей и новой линией
const lineSelect = document.getElementById('lineSelect');
const lineNewInput = document.getElementById('lineNewInput');

if (lineSelect) {
    lineSelect.addEventListener('change', function() {
        if (this.value === '__new__') {
            lineNewInput.style.display = 'block';
            lineNewInput.required = true;
            // Убираем name у select, чтобы не отправлять "__new__"
            lineSelect.removeAttribute('name');
            lineNewInput.setAttribute('name', 'line');
        } else {
            lineNewInput.style.display = 'none';
            lineNewInput.required = false;
            lineNewInput.removeAttribute('name');
            lineSelect.setAttribute('name', 'line');
        }
        // Сохраняем при смене линии
        saveCurrentValues();
    });
}

// Автосохранение при изменении любого поля (опционально, улучшает UX)
document.querySelectorAll('#rated_current, #conductors, #material, #nomenclature, #lineNewInput')
    .forEach(el => {
        if (el) {
            el.addEventListener('change', function() {
                // Для lineNewInput событие change срабатывает после потери фокуса,
                // для селектов — сразу при выборе
                saveCurrentValues();
            });
            // Дополнительно для input: сохраняем при вводе (но не каждый символ, а по потере фокуса)
            if (el.tagName === 'INPUT') {
                el.addEventListener('blur', function() {
                    saveCurrentValues();
                });
            }
        }
    });

// ---------- Логика отмены позиций (не связана с сохранением) ----------
let selectedToCancel = [];

function updateCancelUI() {
    const input = document.getElementById('cancelled_ids_input');
    if (input) {
        input.value = selectedToCancel.join(',');
    }
    const cancelForm = document.getElementById('cancelForm');
    if (cancelForm) {
        cancelForm.style.display = selectedToCancel.length > 0 ? 'block' : 'none';
    }
}

document.querySelectorAll('.cancel-item-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        const row = this.closest('tr');
        const id = parseInt(this.getAttribute('data-id'));

        if (row.classList.contains('cancelled-row')) {
            row.classList.remove('cancelled-row');
            selectedToCancel = selectedToCancel.filter(itemId => itemId !== id);
        } else {
            row.classList.add('cancelled-row');
            selectedToCancel.push(id);
        }
        updateCancelUI();
    });
});

// Инициализация UI отмены при загрузке
updateCancelUI();