// src/api/gameApi.js

const API_BASE_URL = 'http://172.31.196.47:9000';
console.log('API Base URL:', API_BASE_URL);

export const fetchGameData = async (nRound = 1) => {
  try {
    const url = `${API_BASE_URL}/api/game-data?n_round=${nRound}`;
    console.log('Fetching from:', url);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (response.status === 404) {
      console.log('Game data not found, initializing game...');
      const initResult = await initGame(nRound);
      console.log('Init result:', initResult);

      // 等待一会儿让游戏初始化完成
      await new Promise(resolve => setTimeout(resolve, 2000));

      // 重试获取数据
      const retryResponse = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!retryResponse.ok) {
        throw new Error(`Failed to fetch data after init: ${retryResponse.status}`);
      }

      return await retryResponse.json();
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching game data:', error);
    throw error;
  }
};

export const initGame = async (nRound = 1, nPlayer = 8) => {
  try {
    const url = `${API_BASE_URL}/api/init-game?n_round=${nRound}&n_player=${nPlayer}`;
    console.log('Initializing game at:', url);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Game initialized:', data);
    return data;
  } catch (error) {
    console.error('Error initializing game:', error);
    throw error;
  }
};