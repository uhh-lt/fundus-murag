export const userImageApiService = {
  async storeUserImage(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch('/api/data/user_image/store', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to store user image');
    }
    return response.json();
  },
  async getUserImage(userImageId: string): Promise<string> {
    const response = await fetch(`/api/data/user_image/${userImageId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch user image with ID ${userImageId}`);
    }
    return response.json();
  }
};

export default userImageApiService;
