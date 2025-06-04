/**
 * Script JavaScript spécialisé pour les fonctionnalités du blog
 */

// Initialisation spécifique au blog
document.addEventListener('DOMContentLoaded', function() {
    initializeBlogFeatures();
    initializeComments();
    initializeSearch();
    initializeLikeSystem();
});

/**
 * Fonctionnalités spécifiques au blog
 */
function initializeBlogFeatures() {
    // Lecture estimée des articles
    calculateReadingTime();
    
    // Partage social
    initializeSocialShare();
    
    // Table des matières automatique
    generateTableOfContents();
    
    // Copie des liens
    initializeLinkCopy();
}

/**
 * Calcul du temps de lecture estimé
 */
function calculateReadingTime() {
    const articles = document.querySelectorAll('.article-content, .card-text');
    
    articles.forEach(function(article) {
        const text = article.textContent || article.innerText;
        const wordsPerMinute = 200;
        const words = text.trim().split(/\s+/).length;
        const readingTime = Math.ceil(words / wordsPerMinute);
        
        // Créer l'indicateur de temps de lecture
        const readingTimeElement = document.createElement('small');
        readingTimeElement.className = 'reading-time text-muted';
        readingTimeElement.innerHTML = `<i>📖 ${readingTime} min de lecture</i>`;
        
        // L'ajouter avant l'article ou dans le header
        const articleHeader = article.closest('.card')?.querySelector('.card-header');
        if (articleHeader) {
            articleHeader.appendChild(readingTimeElement);
        } else {
            article.parentNode.insertBefore(readingTimeElement, article);
        }
    });
}

/**
 * Partage sur les réseaux sociaux
 */
function initializeSocialShare() {
    const shareButtons = document.querySelectorAll('.share-button');
    
    if (shareButtons.length === 0) {
        // Créer des boutons de partage automatiquement
        const articles = document.querySelectorAll('.article-detail, .card');
        
        articles.forEach(function(article) {
            const shareContainer = document.createElement('div');
            shareContainer.className = 'social-share mt-3';
            shareContainer.innerHTML = `
                <span class="share-label">Partager : </span>
                <button class="btn btn-sm btn-primary share-btn" data-platform="twitter">Twitter</button>
                <button class="btn btn-sm btn-primary share-btn" data-platform="facebook">Facebook</button>
                <button class="btn btn-sm btn-secondary share-btn" data-platform="copy">Copier le lien</button>
            `;
            
            const cardBody = article.querySelector('.card-body');
            if (cardBody) {
                cardBody.appendChild(shareContainer);
            }
        });
    }
    
    // Gérer les clics sur les boutons de partage
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('share-btn')) {
            const platform = e.target.getAttribute('data-platform');
            const url = window.location.href;
            const title = document.title;
            
            shareContent(platform, url, title);
        }
    });
}

/**
 * Partager du contenu sur les plateformes sociales
 */
function shareContent(platform, url, title) {
    let shareUrl = '';
    
    switch (platform) {
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`;
            break;
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
            break;
        case 'copy':
            navigator.clipboard.writeText(url).then(function() {
                showNotification('Lien copié dans le presse-papier !', 'success');
            }).catch(function() {
                // Fallback pour les navigateurs plus anciens
                const textarea = document.createElement('textarea');
                textarea.value = url;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showNotification('Lien copié !', 'success');
            });
            return;
    }
    
    if (shareUrl) {
        window.open(shareUrl, '_blank', 'width=600,height=400');
    }
}

/**
 * Système de commentaires interactif
 */
function initializeComments() {
    // Répondre aux commentaires
    const replyButtons = document.querySelectorAll('.reply-button');
    replyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const commentId = this.getAttribute('data-comment-id');
            toggleReplyForm(commentId);
        });
    });
    
    // Validation des formulaires de commentaires
    const commentForms = document.querySelectorAll('.comment-form');
    commentForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const content = form.querySelector('textarea[name="content"]');
            if (content && content.value.trim().length < 10) {
                e.preventDefault();
                showNotification('Le commentaire doit contenir au moins 10 caractères.', 'warning');
                content.focus();
            }
        });
    });
}

/**
 * Basculer le formulaire de réponse aux commentaires
 */
function toggleReplyForm(commentId) {
    const existingForm = document.querySelector(`#reply-form-${commentId}`);
    
    if (existingForm) {
        existingForm.remove();
        return;
    }
    
    const replyForm = document.createElement('div');
    replyForm.id = `reply-form-${commentId}`;
    replyForm.className = 'reply-form mt-3';
    replyForm.innerHTML = `
        <form method="post" class="comment-form">
            <div class="form-group">
                <textarea name="content" class="form-control" rows="3" 
                         placeholder="Votre réponse..." required></textarea>
            </div>
            <input type="hidden" name="parent_id" value="${commentId}">
            <button type="submit" class="btn btn-primary btn-sm">Répondre</button>
            <button type="button" class="btn btn-secondary btn-sm ml-2" onclick="this.closest('.reply-form').remove()">Annuler</button>
        </form>
    `;
    
    const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`).closest('.comment');
    commentElement.appendChild(replyForm);
    
    replyForm.querySelector('textarea').focus();
}

/**
 * Recherche en temps réel
 */
function initializeSearch() {
    const searchInput = document.querySelector('input[name="search"], input[name="q"]');
    
    if (searchInput) {
        const debouncedSearch = Utils.debounce(performSearch, 300);
        
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            if (query.length >= 3) {
                debouncedSearch(query);
            } else {
                hideSearchResults();
            }
        });
        
        // Fermer les résultats si on clique ailleurs
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-container')) {
                hideSearchResults();
            }
        });
    }
}

/**
 * Effectuer une recherche AJAX
 */
function performSearch(query) {
    const searchUrl = '/search/ajax/'; // À adapter selon votre URL
    
    Ajax.get(`${searchUrl}?q=${encodeURIComponent(query)}`, function(error, data) {
        if (error) {
            console.error('Erreur de recherche:', error);
            return;
        }
        
        displaySearchResults(data.results || []);
    });
}

/**
 * Afficher les résultats de recherche
 */
function displaySearchResults(results) {
    let resultsContainer = document.querySelector('.search-results');
    
    if (!resultsContainer) {
        resultsContainer = document.createElement('div');
        resultsContainer.className = 'search-results';
        resultsContainer.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
        `;
        
        const searchContainer = document.querySelector('.search-container') || 
                               document.querySelector('input[name="search"]').parentNode;
        searchContainer.style.position = 'relative';
        searchContainer.appendChild(resultsContainer);
    }
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="p-3 text-muted">Aucun résultat trouvé</div>';
    } else {
        resultsContainer.innerHTML = results.map(result => `
            <a href="${result.url}" class="search-result-item d-block p-3 text-decoration-none border-bottom">
                <div class="font-weight-bold">${result.title}</div>
                <div class="text-muted small">${Utils.truncateText(result.excerpt, 100)}</div>
            </a>
        `).join('');
    }
    
    resultsContainer.style.display = 'block';
}

/**
 * Masquer les résultats de recherche
 */
function hideSearchResults() {
    const resultsContainer = document.querySelector('.search-results');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
}

/**
 * Système de likes/favoris
 */
function initializeLikeSystem() {
    const likeButtons = document.querySelectorAll('.like-button, .favorite-button');
    
    likeButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const articleId = this.getAttribute('data-article-id');
            const action = this.classList.contains('like-button') ? 'like' : 'favorite';
            
            toggleLike(articleId, action, this);
        });
    });
}

/**
 * Basculer le like/favori
 */
function toggleLike(articleId, action, button) {
    const url = `/articles/${articleId}/${action}/`; // À adapter selon votre URL
    
    Ajax.post(url, {}, function(error, data) {
        if (error) {
            showNotification('Erreur lors de l\'action', 'danger');
            return;
        }
        
        if (data.success) {
            // Mettre à jour l'interface
            const icon = button.querySelector('i') || button;
            const countElement = button.querySelector('.count');
            
            if (data.liked) {
                button.classList.add('active');
                icon.style.color = '#dc3545';
            } else {
                button.classList.remove('active');
                icon.style.color = '';
            }
            
            if (countElement) {
                countElement.textContent = data.count;
            }
            
            showNotification(data.message, 'success');
        }
    });
}

/**
 * Générer une table des matières automatique
 */
function generateTableOfContents() {
    const content = document.querySelector('.article-content');
    const headings = content?.querySelectorAll('h1, h2, h3, h4, h5, h6');
    
    if (!headings || headings.length < 3) return;
    
    const toc = document.createElement('div');
    toc.className = 'table-of-contents card mb-4';
    toc.innerHTML = `
        <div class="card-header">
            <strong>Table des matières</strong>
        </div>
        <div class="card-body">
            <ul class="toc-list"></ul>
        </div>
    `;
    
    const tocList = toc.querySelector('.toc-list');
    
    headings.forEach(function(heading, index) {
        const id = `heading-${index}`;
        heading.id = id;
        
        const li = document.createElement('li');
        li.className = `toc-item toc-${heading.tagName.toLowerCase()}`;
        li.innerHTML = `<a href="#${id}" class="toc-link">${heading.textContent}</a>`;
        
        tocList.appendChild(li);
    });
    
    // Insérer la table des matières au début du contenu
    content.parentNode.insertBefore(toc, content);
    
    // Smooth scroll pour les liens de la table des matières
    toc.addEventListener('click', function(e) {
        if (e.target.classList.contains('toc-link')) {
            e.preventDefault();
            const targetId = e.target.getAttribute('href').substring(1);
            Utils.scrollTo(`#${targetId}`);
        }
    });
}

/**
 * Copie de liens
 */
function initializeLinkCopy() {
    const headings = document.querySelectorAll('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]');
    
    headings.forEach(function(heading) {
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-link-btn';
        copyButton.innerHTML = '🔗';
        copyButton.title = 'Copier le lien vers cette section';
        copyButton.style.cssText = `
            margin-left: 0.5rem;
            background: none;
            border: none;
            cursor: pointer;
            opacity: 0.5;
            transition: opacity 0.3s;
        `;
        
        copyButton.addEventListener('click', function() {
            const url = `${window.location.origin}${window.location.pathname}#${heading.id}`;
            navigator.clipboard.writeText(url).then(function() {
                showNotification('Lien copié !', 'success');
            });
        });
        
        heading.appendChild(copyButton);
        
        // Afficher le bouton au survol
        heading.addEventListener('mouseenter', () => copyButton.style.opacity = '1');
        heading.addEventListener('mouseleave', () => copyButton.style.opacity = '0.5');
    });
}

/**
 * Afficher une notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1050;
        min-width: 250px;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); }
        to { transform: translateX(100%); }
    }
    
    .toc-h1 { margin-left: 0; }
    .toc-h2 { margin-left: 1rem; }
    .toc-h3 { margin-left: 2rem; }
    .toc-h4 { margin-left: 3rem; }
    .toc-h5 { margin-left: 4rem; }
    .toc-h6 { margin-left: 5rem; }
    
    .toc-link {
        text-decoration: none;
        color: #007bff;
        display: block;
        padding: 0.25rem 0;
    }
    
    .toc-link:hover {
        text-decoration: underline;
    }
    
    .search-result-item:hover {
        background-color: #f8f9fa;
    }
`;
document.head.appendChild(style);