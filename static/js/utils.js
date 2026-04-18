const transformImage = (url, width=320) => {
    if (!url) return null;
    try{
        return url.replace("https://files.cpcnewhaven.org",`https://files.cpcnewhaven.org/cdn-cgi/image/width=${width}`);
    } catch (error) {
        console.error("Error transforming image URL:", url, error);
        return url;
    }
};