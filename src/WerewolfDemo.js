import React, { useState, useEffect, useRef } from "react";
import { Play, Pause, SkipForward, SkipBack, User } from "lucide-react";
import { MenuItem, Select, Avatar } from "@mui/material";
import DialogModal from "./components/DialogModal.jsx";
import "./WerewolfDemo.css";
import woodFrame from "./assets/woodFrame2.jpg";
import Guard from "./assets/avatars/Guard.jpg";
import Villager from "./assets/avatars/Villager.jpg";
import Witch from "./assets/avatars/Witch.jpg";
import wereWolf from "./assets/avatars/wereWolf.jpg";
import Seer from "./assets/avatars/Seer.jpg";
import Moderator from "./assets/avatars/start.jpg";

const WerewolfDemo = () => {
  const [currentRound, setCurrentRound] = useState(1);
  const [curUser, setCurUser] = useState("");
  const [dialogModalVisible, setDialogModalVisible] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const messagesEndRef = useRef(null);
  const [gameData, setGameData] = useState({
    players: [],
    dialogue: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch game data from backend
  useEffect(() => {
    const fetchGameData = async () => {
      try {
        const response = await fetch("http://localhost:9000/api/game-data");
        if (!response.ok) {
          throw new Error("Failed to fetch game data");
        }
        const data = await response.json();
        console.log("data", data);
        setGameData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchGameData();
  }, []);

  const roleColors = {
    Guard: "bg-blue-100",
    Seer: "bg-purple-100",
    Werewolf: "bg-red-100",
    Villager: "bg-green-100",
    Witch: "bg-yellow-100",
    Moderator: "bg-gray-100",
  };

  const roleAvatar = {
    Guard: Guard,
    Villager: Villager,
    Seer: Seer,
    Werewolf: wereWolf,
    Witch: Witch,
    Moderator: Moderator,
  };

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 处理自动播放
  useEffect(() => {
    let timer;
    if (isPlaying && currentStep < gameData.dialogue.length - 1) {
      timer = setTimeout(() => {
        setCurrentStep((prev) => prev + 1);
      }, 2000);
    } else if (currentStep >= gameData.dialogue.length - 1) {
      setIsPlaying(false);
    }
    return () => clearTimeout(timer);
  }, [isPlaying, currentStep, gameData.dialogue.length]);

  // 当消息更新时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [currentStep]);

  const handleUserChange = (event) => {
    console.log("user", event.target);
    setCurUser(event.target.value);
  };

  const onClickPlayer = (event) => {
    console.log("event", event);
    const { id, name, role } = event;
    if (role === "Werewolf") {
      // 开对话弹窗
      setDialogModalVisible(true);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-screen text-red-500">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="p-6 mx-6 rounded-lg ">
      {/* <div style={{ display: 'flex', flexDirection: 'column'}}>
        <h3 className="text-lg font-semibold mb-4 text-left text-yellow-400">Player Role</h3>
        <Select style={{ width: '250px' }} value={curUser} onChange={handleUserChange}>
          {gameData.players.map(player => (
            <MenuItem value={player.name}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <User className="h-5 w-5" />
                <div style={{ flex: 1, marginLeft: '10px' }}>
                  <div className="font-medium text-left">{player.name}</div>
                  <div className="text-sm text-gray-500 text-left">{player.role}</div>
                </div>
              </div>
            </MenuItem>
          ))}
        </Select>
      </div> */}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* 左侧玩家列表 */}
        <div className="p-4 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4 text-left text-antiquewhite">
            Player List
          </h3>
          <div className="space-y-3">
            {gameData.players.map((player) => (
              <div
                key={player.id}
                onClick={() => onClickPlayer(player)}
                className="role-card"
              >
                <div className="player-content">
                  <div
                    className={`h-8 w-8 rounded-full ${roleColors[player.role]} flex items-center justify-center flex-shrink-0`}
                  >
                    {/* <User className="h-5 w-5" /> */}
                    <Avatar alt={player.name} src={roleAvatar[player.role]} />
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="font-medium text-left text-yellow-400">
                      {player.name}
                    </div>
                    <div className={`role-style ${player.role}`}>
                      {player.role}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 中间对话展示区 */}
        <div className="md:col-span-3">
          <h3 className="text-lg font-semibold mb-4 text-left text-antiquewhite">
            Game Progress
          </h3>
          <div
            className="p-4 mx-6 rounded-lg shadow-md mb-4 overflow-y-auto"
            style={{ height: "80vh" }}
          >
            <div className="space-y-4">
              {gameData.dialogue
                .slice(0, currentStep + 1)
                .map((message, index) => {
                  const player = gameData.players.find(
                    (p) => p.name === message.speaker,
                  );
                  return (
                    <div
                      key={index}
                      className="flex space-x-3 bg-white bg-opacity-50"
                    >
                      <div className="flex-shrink-0">
                        <div
                          className={`h-8 w-8 rounded-full ${roleColors[player.role]} flex items-center justify-center`}
                        >
                          {/* <User className="h-5 w-5" /> */}
                          <Avatar
                            alt={player.name}
                            src={roleAvatar[player.role]}
                          />
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-baseline text-left">
                          <span className="font-medium text-yellow-400">
                            {message.speaker}
                          </span>
                          <span className={`ml-2 text-sm ${player.role}`}>
                            {player.role}
                          </span>
                          <span className="ml-2 text-xs text-gray-400">
                            {message.type}
                          </span>
                        </div>
                        <div className="mt-1 text-sm text-gray-100 text-left">
                          {message.content}
                        </div>
                      </div>
                    </div>
                  );
                })}
              {/* 添加一个空的div作为滚动目标 */}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 控制栏 */}
          <div className="p-4 mx-6 rounded-lg shadow-md bg-white bg-opacity-50">
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => {
                  setCurrentStep(Math.max(0, currentStep - 1));
                  setIsPlaying(false);
                }}
                className="p-2 rounded-full hover:bg-gray-100"
                disabled={currentStep === 0}
              >
                <SkipBack className="h-6 w-6" />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2 rounded-full hover:bg-gray-100"
                disabled={currentStep >= gameData.dialogue.length - 1}
              >
                {isPlaying ? (
                  <Pause className="h-6 w-6" />
                ) : (
                  <Play className="h-6 w-6" />
                )}
              </button>
              <button
                onClick={() => {
                  setCurrentStep(
                    Math.min(gameData.dialogue.length - 1, currentStep + 1),
                  );
                  setIsPlaying(false);
                }}
                className="p-2 rounded-full hover:bg-gray-100"
                disabled={currentStep >= gameData.dialogue.length - 1}
              >
                <SkipForward className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* <DialogModal /> */}
    </div>
  );
};

export default WerewolfDemo;
