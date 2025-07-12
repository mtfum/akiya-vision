// Global state
let selectedHouseId = null;
let selectedImageId = null;
let selectedImageData = null;
let houses = [];
let lastSelectedStyle = null;

// HTML escape function to prevent XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Toggle mobile menu
function toggleMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('hidden');
}

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    await loadHouses();
    setupEventListeners();
});

// Load houses from API
async function loadHouses() {
    try {
        const response = await fetch('/api/houses');
        houses = await response.json();
        renderHouses();
    } catch (error) {
        console.error('Failed to load houses:', error);
        showError('物件データの読み込みに失敗しました');
    }
}

// Render house cards
function renderHouses() {
    const grid = document.getElementById('houseGrid');
    grid.innerHTML = houses.map(house => `
        <div class="bg-white rounded-lg shadow-md hover:shadow-lg transition cursor-pointer" 
             onclick="selectHouse('${escapeHtml(house.id)}')">
            <div class="p-6">
                <h3 class="text-xl font-semibold mb-2">${escapeHtml(house.name)}</h3>
                <p class="text-gray-600 mb-4">${escapeHtml(house.address)}</p>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="font-medium">価格:</span>
                        <span class="text-blue-600 font-bold">${escapeHtml(house.price)}</span>
                    </div>
                    <div>
                        <span class="font-medium">面積:</span>
                        <span>${escapeHtml(house.area)}</span>
                    </div>
                    <div>
                        <span class="font-medium">築年数:</span>
                        <span>${escapeHtml(house.age)}</span>
                    </div>
                </div>
                <p class="text-gray-600 text-sm mt-4">${escapeHtml(house.description)}</p>
            </div>
        </div>
    `).join('');
}

// Select a house
async function selectHouse(houseId) {
    selectedHouseId = houseId;
    selectedImageId = null;
    selectedImageData = null;
    const house = houses.find(h => h.id === houseId);
    
    if (!house) return;
    
    // Update house details
    document.getElementById('houseName').textContent = house.name;
    document.getElementById('houseAddress').textContent = house.address;
    document.getElementById('housePrice').textContent = house.price;
    document.getElementById('houseArea').textContent = house.area;
    document.getElementById('houseAge').textContent = house.age;
    document.getElementById('houseDescription').textContent = house.description;
    
    // Load demo images for this house type
    await loadDemoImages(houseId);
    
    // Hide renovation section until image is selected
    document.getElementById('renovationSection').classList.add('hidden');
    
    // Show house details section
    document.getElementById('houseDetails').classList.remove('hidden');
    
    // Scroll to details
    document.getElementById('houseDetails').scrollIntoView({ behavior: 'smooth' });
}

// Load demo images for selected house
async function loadDemoImages(houseId) {
    try {
        const response = await fetch(`/api/demo-images/${houseId}`);
        const demoImages = await response.json();
        
        const container = document.getElementById('demoImages');
        container.innerHTML = demoImages.map(img => `
            <div class="cursor-pointer hover:opacity-80 transition" onclick="selectDemoImage('${escapeHtml(img.url)}', '${escapeHtml(img.name)}', '${escapeHtml(img.id)}')">
                <img src="${escapeHtml(img.url)}" alt="${escapeHtml(img.name)}" class="w-full h-24 object-cover rounded-lg demo-image" data-id="${escapeHtml(img.id)}">
                <p class="text-xs text-center mt-1 text-gray-600">${escapeHtml(img.name)}</p>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load demo images:', error);
    }
}

// Select a demo image
function selectDemoImage(imageUrl, imageName, imageId) {
    // For demo, we'll use the URL directly instead of converting to base64
    selectedImageData = imageUrl;
    selectedImageId = 'demo-' + Date.now();
    
    // Remove previous selection
    document.querySelectorAll('.demo-image').forEach(img => {
        img.classList.remove('demo-image-selected');
    });
    
    // Highlight selected image
    const selectedImg = document.querySelector(`.demo-image[data-id="${imageId}"]`);
    if (selectedImg) {
        selectedImg.classList.add('demo-image-selected');
    }
    
    // Show renovation section
    document.getElementById('renovationSection').classList.remove('hidden');
    
    // Scroll to renovation section
    document.getElementById('renovationSection').scrollIntoView({ behavior: 'smooth' });
}

// Setup event listeners
function setupEventListeners() {
    // Setup before/after slider
    setupSlider();
}


// Generate renovation
async function generateRenovation(style) {
    if (!selectedHouseId || !selectedImageId) {
        showError('画像を選択してください');
        return;
    }
    
    // Store the selected style
    lastSelectedStyle = style;
    
    try {
        // Show loading state
        document.getElementById('resultsSection').classList.remove('hidden');
        document.getElementById('loadingState').classList.remove('hidden');
        document.getElementById('sliderContainer').classList.add('hidden');
        
        // Disable all style buttons
        document.querySelectorAll('.style-button').forEach(btn => {
            btn.disabled = true;
            btn.classList.add('opacity-50');
        });
        
        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
        
        const response = await fetch(`/api/renovate/${selectedHouseId}/${selectedImageId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                style: style,
                image_url: selectedImageData  // Include the image URL/data
            })
        });
        
        if (!response.ok) {
            throw new Error('Generation failed');
        }
        
        const result = await response.json();
        
        // Use the stored image data instead of looking it up
        if (!selectedImageData) {
            throw new Error('Original image data not found');
        }
        
        // Display before/after (original first, then generated)
        displayBeforeAfter(selectedImageData, result.output[0]);
        
        // Enable buttons
        document.querySelectorAll('.style-button').forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('opacity-50');
        });
        
    } catch (error) {
        console.error('Generation failed:', error);
        showError('画像の生成に失敗しました');
        
        // Hide loading and enable buttons
        document.getElementById('loadingState').classList.add('hidden');
        document.querySelectorAll('.style-button').forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('opacity-50');
        });
    }
}

// Display before/after comparison
function displayBeforeAfter(beforeUrl, afterUrl) {
    // Set images correctly: bottom layer = before (original), top clipped layer = after (generated)
    // This way sliding left reveals more of the before image
    document.getElementById('beforeImage').src = beforeUrl;  // Original image as base
    document.getElementById('afterImage').src = afterUrl;    // Generated image on top (clipped)
    
    // Hide loading, show slider
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('sliderContainer').classList.remove('hidden');
    
    // Start slider from the left to show the "Before" image first
    const slider = document.getElementById('beforeAfterSlider');
    const divider = slider.querySelector('.slider-divider');
    const afterContainer = slider.querySelector('.overflow-hidden');
    
    // Position at far left to show before image first
    divider.style.left = '0%';
    afterContainer.style.clipPath = 'inset(0 100% 0 0)';
}

// Setup before/after slider
function setupSlider() {
    const slider = document.getElementById('beforeAfterSlider');
    const divider = slider.querySelector('.slider-divider');
    const afterContainer = slider.querySelector('.overflow-hidden');
    
    let isDragging = false;
    
    const startDrag = (e) => {
        isDragging = true;
        e.preventDefault();
    };
    
    const drag = (e) => {
        if (!isDragging) return;
        
        const rect = slider.getBoundingClientRect();
        const x = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        const position = ((x - rect.left) / rect.width) * 100;
        
        // Clamp between 0 and 100
        const clampedPosition = Math.max(0, Math.min(100, position));
        
        divider.style.left = `${clampedPosition}%`;
        afterContainer.style.clipPath = `inset(0 ${100 - clampedPosition}% 0 0)`;
    };
    
    const endDrag = () => {
        isDragging = false;
    };
    
    // Mouse events
    divider.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', endDrag);
    
    // Touch events
    divider.addEventListener('touchstart', startDrag);
    document.addEventListener('touchmove', drag);
    document.addEventListener('touchend', endDrag);
    
    // Click to position
    slider.addEventListener('click', (e) => {
        const rect = slider.getBoundingClientRect();
        const position = ((e.clientX - rect.left) / rect.width) * 100;
        const clampedPosition = Math.max(0, Math.min(100, position));
        
        divider.style.left = `${clampedPosition}%`;
        afterContainer.style.clipPath = `inset(0 ${100 - clampedPosition}% 0 0)`;
    });
}

// Show error message
function showError(message) {
    // Simple alert for now, could be replaced with better UI
    alert(message);
}

// Show Before image completely
function showBeforeImage() {
    const slider = document.getElementById('beforeAfterSlider');
    const divider = slider.querySelector('.slider-divider');
    const afterContainer = slider.querySelector('.overflow-hidden');
    
    // Animate to show full Before image (left side)
    animateSlider(divider, afterContainer, 0);
}

// Show After image completely
function showAfterImage() {
    const slider = document.getElementById('beforeAfterSlider');
    const divider = slider.querySelector('.slider-divider');
    const afterContainer = slider.querySelector('.overflow-hidden');
    
    // Animate to show full After image (right side)
    animateSlider(divider, afterContainer, 100);
}

// Animate slider to target position
function animateSlider(divider, afterContainer, targetPercent) {
    // Get current position
    const currentLeft = parseFloat(divider.style.left) || 0;
    const duration = 300; // Animation duration in ms
    const startTime = Date.now();
    
    function animate() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeInOut = progress < 0.5 
            ? 2 * progress * progress 
            : 1 - Math.pow(-2 * progress + 2, 2) / 2;
        
        // Calculate current position
        const currentPos = currentLeft + (targetPercent - currentLeft) * easeInOut;
        
        // Update positions
        divider.style.left = `${currentPos}%`;
        afterContainer.style.clipPath = `inset(0 ${100 - currentPos}% 0 0)`;
        
        // Continue animation if not complete
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}

// Show inquiry form modal
function showInquiryForm() {
    document.getElementById('inquiryModal').classList.remove('hidden');
}

// Close inquiry form modal
function closeInquiryForm() {
    document.getElementById('inquiryModal').classList.add('hidden');
}

// Submit inquiry
function submitInquiry(event) {
    event.preventDefault();
    
    // Get form data
    const formData = {
        name: document.getElementById('name').value.trim(),
        email: document.getElementById('email').value.trim(),
        phone: document.getElementById('phone').value.trim(),
        message: document.getElementById('message').value.trim(),
        houseId: selectedHouseId,
        imageId: selectedImageId,
        selectedStyle: lastSelectedStyle
    };
    
    // Validate form data
    if (!formData.name || formData.name.length > 100) {
        alert('お名前を正しく入力してください（100文字以内）');
        return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email || !emailRegex.test(formData.email) || formData.email.length > 255) {
        alert('メールアドレスを正しく入力してください');
        return;
    }
    
    // Phone validation (optional, but if provided must be valid)
    if (formData.phone) {
        const phoneRegex = /^[\d\-\+\(\)\s]+$/;
        if (!phoneRegex.test(formData.phone) || formData.phone.length > 20) {
            alert('電話番号を正しく入力してください');
            return;
        }
    }
    
    // Message validation
    if (formData.message && formData.message.length > 1000) {
        alert('メッセージは1000文字以内で入力してください');
        return;
    }
    
    // In a real application, you would send this to a backend
    console.log('Inquiry submitted:', formData);
    
    // Show success message
    alert('お問い合わせありがとうございます。担当者より連絡させていただきます。');
    
    // Close modal and reset form
    closeInquiryForm();
    event.target.reset();
}

// Make functions globally accessible for onclick handlers
window.selectHouse = selectHouse;
window.selectDemoImage = selectDemoImage;
window.generateRenovation = generateRenovation;
window.showBeforeImage = showBeforeImage;
window.showAfterImage = showAfterImage;
window.showInquiryForm = showInquiryForm;
window.closeInquiryForm = closeInquiryForm;
window.submitInquiry = submitInquiry;
window.toggleMenu = toggleMenu;