import React, { useState } from "react";
import { TextField, Box, Select, MenuItem, Button} from "@mui/material";
import { Container } from "lucide-react";
import "./gameConfig.css"

const GameConfig = ({
    handleStep
}) => {
    const [rounds, setRounds] = useState(null)
    const [number, setNumber] = useState(null)

    return (
        <div className="config-form">
            <h3 className="text-lg font-semibold mb-4 text-left text-antiquewhite">GAME CONFIGURE</h3>
            <div className="form-item">
                <div className="font-medium text-left text-yellow-400" style={{ width: '230px'}}>rounds: </div>
                <TextField
                    // color="secondary" 
                    // focused
                    type="number"
                    margin="normal"
                    value={rounds}
                    InputProps={{
                        style: {
                            color: 'white',
                            fontSize: '20px',
                        }
                    }}
                    className="text-input"
                    sx={{
                        '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'white',
                        }
                    }}
                    onChange={(e) => setRounds(e.target.value)}
                />
            </div>
            <div className="form-item">
                <div className="font-medium text-left text-yellow-400" style={{ width: '230px'}}>player_number: </div>
                <TextField
                    select
                    value={number} 
                    onChange={(e) => setNumber(e.target.value)} 
                    InputProps={{
                        style: {
                            color: 'white',
                            fontSize: '20px',
                        }
                    }}
                    sx={{
                        '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'white',
                        }
                    }}
                    className="text-input"
                >
                    {[5, 6, 7, 8, 9, 10].map(num => (
                        <MenuItem key={num} value={num}>{num}</MenuItem>
                    ))}
                </TextField>
            </div>
            <div className="form-item">
                <Button style={{ fontSize: '18px', fontWeight: 'bold', color: 'white' }} onClick={(e) => {handleStep(1)}}>下一步</Button>
            </div>
        </div>
    )
}

export default GameConfig